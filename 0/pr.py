import sys
import socket

class netcat(cmd.Cmd):
    prompt = "cmd>> "
    def __init__(self, *ap, socket = None):
        self.socket = socket
        super().__init__(*ap, **kwargs)
    def do_print(self, arg):
        self.socket.sendall(f"print {arg}\n".encode())
        self.response()
    def do_info(self, arg):
        self.socket.sendall(f"info

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    while msg := sys.stdin.buffer.readline():
        s.sendall(msg)
        print(s.recv(1024).rstrip().decode())

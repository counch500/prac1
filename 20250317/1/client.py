import socket
import cowsay

class MudClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', 12345))

    def send_command(self, command):
        self.sock.sendall(command.encode())
        response = self.sock.recv(1024).decode()
        return response

    def move(self, x, y):
        response = self.send_command(f"move {x} {y}")
        if response.startswith("encounter"):
            _, name, hello = response.split(maxsplit=2)
            print(cowsay.cowsay(hello, cow=name))
        else:
            print(response)

    def addmon(self, name, x, y, hello, hp):
        response = self.send_command(f"addmon {name} {x} {y} {hello} {hp}")
        print(response)

    def attack(self, name, weapon):
        response = self.send_command(f"attack {name} {weapon}")
        print(response)

def main():
    client = MudClient()
    while True:
        command = input("> ")
        if command.startswith("move"):
            _, x, y = command.split()
            client.move(int(x), int(y))
        elif command.startswith("addmon"):
            _, name, x, y, hello, hp = command.split()
            client.addmon(name, int(x), int(y), hello, int(hp))
        elif command.startswith("attack"):
            _, name, weapon = command.split()
            client.attack(name, weapon)
        else:
            print("Invalid command")

if __name__ == "__main__":
    main()

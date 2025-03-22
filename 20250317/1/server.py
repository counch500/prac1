import socket

class MudServer:
    def __init__(self):
        self.player_position = [0, 0]
        self.monsters = {}

    def handle_command(self, command):
        parts = command.split()
        if not parts:
            return "Invalid command"

        cmd = parts[0]
        if cmd == "move":
            x, y = map(int, parts[1:])
            self.player_position = [x, y]
            if (x, y) in self.monsters:
                name, hello, hp = self.monsters[(x, y)]
                return f"encounter {name} {hello}"
            return f"moved {x} {y}"
        elif cmd == "addmon":
            name, x, y, hello, hp = parts[1], int(parts[2]), int(parts[3]), parts[4], int(parts[5])
            self.monsters[(x, y)] = (name, hello, hp)
            return f"added {name} {x} {y} {hello} {hp}"
        elif cmd == "attack":
            name, weapon = parts[1], parts[2]
            x, y = self.player_position
            if (x, y) in self.monsters and self.monsters[(x, y)][0] == name:
                _, _, hp = self.monsters[(x, y)]
                damage = 10 if weapon == "sword" else 15 if weapon == "spear" else 20
                hp -= damage
                if hp <= 0:
                    del self.monsters[(x, y)]
                    return f"killed {name}"
                else:
                    self.monsters[(x, y)] = (name, _, hp)
                    return f"attacked {name} {damage} {hp}"
            return f"no_monster {name}"
        return "Invalid command"

def start_server():
    server = MudServer()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 12345))
        s.listen()
        print("Server started on localhost:12345")
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break
                response = server.handle_command(data)
                conn.sendall(response.encode())

if __name__ == "__main__":
    start_server()

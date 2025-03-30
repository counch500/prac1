import cmd
import shlex
import cowsay
import socket
import sys
import threading
import readline

class GameError(Exception):
    def __init__(self, code, name=''):
        self.message = ["Invalid arguments", "Cannot add unknown monster",
                       f"No {name} here", "Unknown weapon"][code-1]

class MUDClient(cmd.Cmd):
    prompt = 'MUD> '
    host = "localhost"
    port = 1337

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))
        self.socket.sendall(f"{username}\n".encode())
        response = self.socket.recv(1024).decode().strip()
        if response == "Username already taken":
            print("This username is already taken")
            sys.exit(1)
        print(response)
        self.monsters = set()
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def receive_messages(self):
        while True:
            try:
                msg = self.socket.recv(4096).decode()
                if not msg:
                    print("\nConnection lost. Exiting...")
                    break
                msg = msg.rstrip()
                if msg:
                    current_input = readline.get_line_buffer()
                    sys.stdout.write(f"\r{msg}\n{self.prompt}{current_input}")
                    sys.stdout.flush()
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                break
            except Exception as e:
                print(f"\nError: {e}")
                break

    def handle_addmon_response(self, name, x, y, hello):
        response = self.socket.recv(1024).rstrip().decode()
        if response == "cannot add monster to player's position":
            print(response)
            return
        print(f"Added monster {name} to ({x}, {y}) saying {hello}")
        if response == '1':
            print("Replaced the old monster")
        self.monsters.add(name)

    def handle_attack_response(self, name):
        response = self.socket.recv(1024).rstrip().decode()
        if response == 'no':
            print(f"No {name} here")
            return
        if not response:
            print("empty response")
            return
        damage, hp = map(int, response.split())
        print(f"Attacked {name}, damage {damage} hp")
        print(f"{name} died" if hp == 0 else f"{name} now has {hp}")

    def handle_move_response(self):
        response = self.socket.recv(4096).decode().strip().split("\n", 1)
        print(f"Moved to ({response[0]})")
        if len(response) > 1:
            print(response[1])

    def do_addmon(self, args):
        try:
            x, y, hp, hello, name = self.validate_addmon_args(args)
            try:
                self.socket.sendall(f"addmon {name} {x} {y} {hp} {hello}\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True
        except GameError as e:
            print(e.message)

    def do_attack(self, args):
        try:
            weapon, name = self.validate_attack_args(args)
            try:
                self.socket.sendall(f"attack {weapon} {name}\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True
        except GameError as e:
            print(e.message)

    def do_up(self, args):
        self._move(args, "0 -1")

    def do_down(self, args):
        self._move(args, "0 1") 

    def do_left(self, args):
        self._move(args, "-1 0")

    def do_right(self, args):
        self._move(args, "1 0")

    def _move(self, args, coords):
        if args:
            print(GameError(1).message)
        else:
            try:
                self.socket.sendall(f"move {coords}\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True

    def default(self, args):
        print("Invalid command")

    def complete_addmon(self, text, line, begidx, endidx):
        words = (line[:endidx] + ".").split()
        options = list({'hello', 'hp', 'coords'} - set(line[:endidx].split()))
        condition = (len(words) % 2 == 0) if 'coords' in words and words[-2] != 'coords' else (len(words) % 2 == 1)
        if len(words) == 2:
            options = cowsay.list_cows() + ["jgsbat"]
        elif not condition:
            options = []
        return [c for c in options if c.startswith(text)]

    def complete_attack(self, text, line, begidx, endidx):
        parts = line.split()
        if len(parts) <= 2:
            return [m for m in cowsay.list_cows() + ["jgsbat"] if m.startswith(text)]
        elif len(parts) >= 3 and parts[-2] == "with":
            return [w for w in ["sword", "spear", "axe"] if w.startswith(text)]
        return []

    def validate_addmon_args(self, args):
        parts = shlex.split(args)
        if len(parts) != 8:
            raise GameError(1)
        name = parts[0]
        parsed = parse_args(parts[1:], {"hello": 1, "hp": 1, "coords": 2})
        if not parsed:
            raise GameError(1)
        x, y = parsed['coords']
        hello = parsed['hello'][0]
        hp = parsed['hp'][0]
        if not x.isdigit() or not y.isdigit() or not hp.isdigit():
            raise GameError(1)
        x, y, hp = map(int, [x, y, hp])
        if x < 0 or x >= 10 or y < 0 or y >= 10 or hp <= 0:
            raise GameError(1)
        if name not in cowsay.list_cows() + ["jgsbat"]:
            raise GameError(2)
        return x, y, hp, hello, name

    def validate_attack_args(self, args):
        parts = shlex.split(args)
        parsed = parse_args(parts, {'with': 1})
        weapon = parsed["with"][0] if parsed else "sword"
        if weapon not in ["sword", "spear", "axe"]:
            raise GameError(4)
        if not parts or parts[0] not in cowsay.list_cows() + ["jgsbat"]:
            raise GameError(1)
        return weapon, parts[0]

def parse_args(args, params):
    result = {}
    for param in params:
        if param not in args:
            return None
        result[param] = args[args.index(param)+1 : args.index(param)+1+params[param]]
    return result

if __name__ == '__main__':
    print("<<< Welcome to Python-MUD 0.1 >>>")
    if len(sys.argv) < 2:
        print("Usage: python client.py <username>")
        sys.exit(1)
    MUDClient(sys.argv[1]).cmdloop()

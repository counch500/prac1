"""
Client module for MOOD MUD game.
"""

import cmd
import shlex
import cowsay
import socket
import sys
import threading
import readline


class Error(Exception):
    def __init__(self, code, name=''):
        match code:
            case 1:
                self.text = "Invalid arguments"
            case 2:
                self.text = "Cannot add unknown monster"
            case 3:
                self.text = f"No {name} here"
            case 4:
                self.text = "Unknown weapon"


class Client_MUD(cmd.Cmd):
    prompt = 'MUD> '
    host = "localhost"
    port = 1337

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))

        # Отправляем имя пользователя при подключении
        self.s.sendall(f"{username}\n".encode())
        response = self.s.recv(1024).decode().strip()
        if response == "Username already taken":
            print("This username is already taken")
            sys.exit(1)
        print(response)

        self.monsters = set()

        # Start message receiving thread
        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()

    def do_movemonsters(self, args):
        """Toggle wandering monsters mode
        Usage: movemonsters on|off
        """
        args = args.strip().lower()
        if args not in ["on", "off"]:
            print("Error: please use 'on' or 'off'")
            print("Example: movemonsters off")
            return
            
        try:
            self.s.sendall(f"movemonsters {args}\n".encode())
        except ConnectionError:
            print("\nConnection to server lost")
            return True

    def receive_messages(self):
        while True:
            try:
                message = self.s.recv(4096).decode()
                if not message:
                    print("\nConnection lost. Exiting...")
                    break
            # Strip only trailing whitespace to preserve newlines in cowsay art
                message = message.rstrip()
                if message:
                    current_input = readline.get_line_buffer()
                    sys.stdout.write(f"\r{message}\n{self.prompt}{current_input}")
                    sys.stdout.flush()
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                break
            except Exception as e:
                print(f"\nError: {e}")
                break

    def response_addmon(self, name, x, y, hello):
        response = self.s.recv(1024).rstrip().decode()
        if response == "cannot add monster to player's position":
            print(response)
            return
        print(f"Added monster {name} to ({x}, {y}) saying {hello}")
        if response == '1':
            print("Replaced the old monster")
        self.monsters.add(name)

    def response_attack(self, name):
        response = self.s.recv(1024).rstrip().decode()

        if response == 'no':
            print(f"No {name} here")
            return
        if not response:
            print(f"empty response")
            return
        damage, hp = map(int, response.split())
        print(f"Attacked {name}, damage {damage} hp")
        if hp == 0:
            print(f"{name} died")
        else:
            print(f"{name} now has {hp}")

    def response_move(self):
        response = self.s.recv(4096).decode().strip()
        parts = response.split("\n", 1)
        print(f"Moved to ({parts[0]})")
        if len(parts) > 1:
            print(parts[1])

    def do_addmon(self, args):
        try:
            x, y, hp, hello, name = self.add_monster_check(args)
            try:
                self.s.sendall(f"addmon {name} {x} {y} {hp} {hello}\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True
        except Error as e:
            print(e.text)

    def do_attack(self, args):
        try:
            weapon, name = self.attack_check(args)
            try:
                self.s.sendall(f"attack {weapon} {name}\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True
        except Error as e:
            print(e.text)

    def do_up(self, args):
        if args:
            print(Error(1).text)
        else:
            try:
                self.s.sendall(f"move 0 -1\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True

    def do_down(self, args):
        if args:
            print(Error(1).text)
        else:
            try:
                self.s.sendall(f"move 0 1\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True

    def do_left(self, args):
        if args:
            print(Error(1).text)
        else:
            try:
                self.s.sendall(f"move -1 0\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True

    def do_right(self, args):
        if args:
            print(Error(1).text)
        else:
            try:
                self.s.sendall(f"move 1 0\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True

    def do_sayall(self, args):
        """
        Send a message to all players. Usage: sayall <message> or sayall "message with spaces"
        """
        if not args:
            print("Invalid arguments")
            return
        try:
            self.s.sendall(f"sayall {args}\n".encode())
        except ConnectionError:
            print("\nConnection lost. Exiting...")
            return True

    def default(self, args):
        print("Invalid command")

    def complete_addmon(self, text, line, begidx, endidx):
        words = (line[:endidx] + ".").split()
        DICT = list({'hello', 'hp', 'coords'} - set(line[:endidx].split()))
        if 'coords' in words and words[-2] != 'coords':
            condition = (len(words) % 2 == 0)
        else:
            condition = (len(words) % 2 == 1)
        if len(words) == 2:
            DICT = cowsay.list_cows() + ["jgsbat"]
        elif not condition:
            DICT = []
        return [c for c in DICT if c.startswith(text)]

    def complete_attack(self, text, line, begidx, endidx):
        parts = line.split()
        if len(parts) <= 2:
            monsters = cowsay.list_cows() + ["jgsbat"]
            return [m for m in monsters if m.startswith(text)]
        elif len(parts) >= 3 and parts[-2] == "with":
            return [w for w in ["sword", "spear", "axe"] if w.startswith(text)]
        return []

    def add_monster_check(self, args):
        preprocess = shlex.split(args)
        if len(preprocess) != 8:
            raise Error(1)
        name = preprocess[0]
        parsed_args = parse_args(preprocess[1:], {"hello": 1, "hp": 1, "coords": 2})
        if not parsed_args:
            raise Error(1)
        x, y = parsed_args['coords']
        hello = parsed_args['hello'][0]
        hp = parsed_args['hp'][0]
        if (not x.isdigit() or
            not y.isdigit() or
            not hp.isdigit()):
            raise Error(1)
        x, y, hp = map(int, [x, y, hp])
        if x < 0 or x >= 10 or y < 0 or y >= 10 or hp <= 0:
            raise Error(1)
        if name not in cowsay.list_cows() + ["jgsbat"]:
            raise Error(2)
        return x, y, hp, hello, name

    def attack_check(self, args):
        splitted = shlex.split(args)
        parsed_args = parse_args(splitted, {'with': 1})
        if parsed_args:
            weapon = parsed_args["with"][0]
            if weapon not in ["sword", "spear", "axe"]:
                raise Error(4)
        else:
            weapon = "sword"
        if len(args) == 0 or splitted[0] not in cowsay.list_cows() + ["jgsbat"]:
            raise Error(1)
        name = splitted[0]
        return weapon, name


def parse_args(args, param):
    args_parsed = {}
    for i in param:
        if i not in args:
            return None
        args_parsed[i] = args[args.index(i) + 1: args.index(i) + 1 + param[i]]
    return args_parsed


if __name__ == '__main__':
    print("<<< Welcome to Python-MUD 0.1 >>>")
    if len(sys.argv) < 2:
        print("Usage: python client.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    Client_MUD(username).cmdloop()
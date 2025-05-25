"""MUD (Multi-User Dungeon) game client module.

This module implements a client for the MUD game, allowing players
to connect to the server and interact with the game world.
"""
from importlib.resources import files
import cmd
import shlex
import cowsay
import socket
import sys
import threading
import readline
import time
import argparse
import webbrowser

class Error(Exception):
    """Custom exception class for game errors.

    Attributes:
        text (str): Error message text.
    """

    def __init__(self, code, name=''):
        """Initialize error with code and optional name.

        Args:
            code (int): Error code.
            name (str, optional): Additional name parameter for some errors.
        """
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
    """Command interpreter for MUD client.

    Attributes:
        prompt (str): Command prompt string. Default: 'MUD> '
        host (str): Server hostname. Default: 'localhost'
        port (int): Server port number. Default: 1337
        command_delay (float): Delay between commands in seconds. Default: 1.0
    """

    prompt = 'MUD> '
    host = "localhost"
    port = 1337
    command_delay = 1.0  # Delay between commands in seconds

    def __init__(self, username, input_file=None):
        """Initialize client with username and optional input file.

        Args:
            username (str): Player's username.
            input_file (file, optional): File object for command input.
        """
        super().__init__()
        self.username = username
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))

        self.s.sendall(f"{username}\n".encode())
        response = self.s.recv(1024).decode().strip()
        if response == "Username already taken":
            print("This username is already taken")
            sys.exit(1)
        print(response)

        self.monsters = set()

        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()

        if input_file:
            self.stdin = input_file
            self.prompt = ''
            self.use_rawinput = False

    def do_documentation(self, args):
        """Open generated documentation in browser"""
        docs_path = files("mood").joinpath("docs/build/html/index.html")
        webbrowser.open(f"file://{docs_path}")

    def do_EOF(self, args):
        """Handle end of file/input.

        Args:
            args: Command arguments (unused).

        Returns:
            bool: Always returns True to indicate EOF.
        """
        return True

    def precmd(self, line):
        """Process command before execution.

        Args:
            line (str): Command line to process.

        Returns:
            str: Processed command line.
        """
        time.sleep(self.command_delay)  # Add delay between commands
        return line

    def receive_messages(self):
        """Receive and process messages from server."""
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
        """Process response from addmon command.

        Args:
            name (str): Monster name.
            x (int): X coordinate.
            y (int): Y coordinate.
            hello (str): Monster greeting message.
        """
        response = self.s.recv(1024).rstrip().decode()
        if response == "cannot add monster to player's position":
            print(response)
            return
        print(f"Added monster {name} to ({x}, {y}) saying {hello}")
        if response == '1':
            print("Replaced the old monster")
        self.monsters.add(name)

    def response_attack(self, name):
        """Process response from attack command.

        Args:
            name (str): Monster name.
        """
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
        """Process response from move command."""
        response = self.s.recv(4096).decode().strip()
        parts = response.split("\n", 1)
        print(f"Moved to ({parts[0]})")
        if len(parts) > 1:
            print(parts[1])

    def do_addmon(self, args):
        """Add a monster to the game.

        Usage: addmon <name> <x> <y> <hp> <hello>
        """
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
        """Attack a monster.

        Usage: attack <monster_name> with <weapon>
        """
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
        """Move player up."""
        if args:
            print(Error(1).text)
        else:
            try:
                self.s.sendall(f"move 0 -1\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True

    def do_down(self, args):
        """Move player down."""
        if args:
            print(Error(1).text)
        else:
            try:
                self.s.sendall(f"move 0 1\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True

    def do_left(self, args):
        """Move player left."""
        if args:
            print(Error(1).text)
        else:
            try:
                self.s.sendall(f"move -1 0\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True

    def do_right(self, args):
        """Move player right."""
        if args:
            print(Error(1).text)
        else:
            try:
                self.s.sendall(f"move 1 0\n".encode())
            except ConnectionError:
                print("\nConnection lost. Exiting...")
                return True

    def do_sayall(self, args):
        """Send a message to all players.
        Usage: sayall <message> or sayall "message with spaces"
        """
        if not args:
            print("Invalid arguments")
            return
        try:
            self.s.sendall(f"sayall {args}\n".encode())
        except ConnectionError:
            print("\nConnection lost. Exiting...")
            return True

    def do_movemonsters(self, args):
        """Enable or disable wandering monsters mode.
        Usage: movemonsters on/off
        """
        if args not in ["on", "off"]:
            print("Invalid arguments. Use 'on' or 'off'")
            return
        try:
            self.s.sendall(f"movemonsters {args}\n".encode())
        except ConnectionError:
            print("\nConnection lost. Exiting...")
            return True

    def do_locale(self, args):
        """Set the locale for messages.
        Usage: locale <locale_name>
        """
        if not args:
            print("Invalid arguments. Please specify a locale")
            return
        try:
            self.s.sendall(f"locale {args}\n".encode())
        except ConnectionError:
            print("\nConnection lost. Exiting...")
            return True

    def default(self, args):
        """Handle unknown commands.

        Args:
            args: Command arguments.
        """
        print("Invalid command")

    def complete_addmon(self, text, line, begidx, endidx):
        """Complete addmon command arguments.

        Args:
            text (str): Text to complete.
            line (str): Current command line.
            begidx (int): Start index of text.
            endidx (int): End index of text.

        Returns:
            list: List of possible completions.
        """
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
        """Complete attack command arguments.

        Args:
            text (str): Text to complete.
            line (str): Current command line.
            begidx (int): Start index of text.
            endidx (int): End index of text.

        Returns:
            list: List of possible completions.
        """
        parts = line.split()
        if len(parts) <= 2:
            monsters = cowsay.list_cows() + ["jgsbat"]
            return [m for m in monsters if m.startswith(text)]
        elif len(parts) >= 3 and parts[-2] == "with":
            return [w for w in ["sword", "spear", "axe"] if w.startswith(text)]
        return []

    def add_monster_check(self, args):
        """Validate addmon command arguments.

        Args:
            args (str): Command arguments.

        Returns:
            tuple: Validated arguments (x, y, hp, hello, name).

        Raises:
            Error: If arguments are invalid.
        """
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
        """Validate attack command arguments.

        Args:
            args (str): Command arguments.

        Returns:
            tuple: Validated arguments (weapon, name).

        Raises:
            Error: If arguments are invalid.
        """
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
    """Parse command arguments.

    Args:
        args (list): List of arguments.
        param (dict): Parameter specifications.

    Returns:
        dict: Parsed arguments or None if invalid.
    """
    args_parsed = {}
    for i in param:
        if i not in args:
            return None
        args_parsed[i] = args[args.index(i) + 1: args.index(i) + 1 + param[i]]
    return args_parsed

def main():
    """Main entry point for the client."""
    parser = argparse.ArgumentParser(description='MUD game client')
    parser.add_argument('username', help='Player username')
    parser.add_argument('--file', help='Command file to execute')
    args = parser.parse_args()

    input_file = None
    if args.file:
        try:
            input_file = open(args.file, 'r')
        except IOError:
            print(f"Error: Could not open file {args.file}")
            sys.exit(1)

    client = Client_MUD(args.username, input_file)
    try:
        client.cmdloop()
    finally:
        if input_file:
            input_file.close()

if __name__ == '__main__':
    main()

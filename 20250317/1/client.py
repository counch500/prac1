import cmd
import shlex
import cowsay
import socket
from io import StringIO

cows = cowsay.list_cows() + ['jgsbat']

jgsbat = cowsay.read_dot_cow(StringIO(r"""
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\\--//|.'-._  (
     )'   .'\/o\/o\/'.   `(
      ) .' . \====/ . '. (
       )  / <<    >> \  (
        '-._/``  ``\_.-'
  jgs     __\\\'--'//__
         (((""`  `"")))
"""))

class Client_MUD(cmd.Cmd):
    prompt = 'MUD> '
    host = "localhost"
    port = 12345

    def __init__(self):
        super().__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))

    def send_command(self, command):
        print(f"Sending: {command}")
        self.s.sendall(command.encode())
        response = self.s.recv(1024).decode()
        print(f"Received: {response}")
        return response

    def do_move(self, arg):
        "Move the player: move <direction>"
        if arg not in ["up", "down", "left", "right"]:
            print("Invalid direction. Use 'up', 'down', 'left', or 'right'.")
            return

        response = self.send_command(f"move {arg}")
        if not response:
            print("No response from server.")
            return

        if "encounter" in response:
            moved, encounter = response.split("\n")
            x, y = moved.split()[1:]
            print(f"Moved to ({x}, {y})")
            name, hello = encounter.split()[1:]
            if name == "jgsbat":
                print(cowsay.cowsay(hello, cowfile=jgsbat))
            else:
                print(cowsay.cowsay(hello, cow=name))
        else:
            x, y = response.split()[1:]
            print(f"Moved to ({x}, {y})")

    def do_addmon(self, arg):
        "Add a monster: addmon <name> <x> <y> <hello> <hp>"
        try:
            name, x, y, hello, hp = shlex.split(arg)
            x, y, hp = int(x), int(y), int(hp)
            if name not in cows:
                print(f"Cannot add unknown monster: {name}")
                return
            response = self.send_command(f"addmon {name} {x} {y} {hello} {hp}")
            print(response)
        except ValueError:
            print("Invalid arguments. Usage: addmon <name> <x> <y> <hello> <hp>")

    def do_attack(self, arg):
        "Attack a monster: attack <name> [with <weapon>]"
        parts = shlex.split(arg)
        if not parts:
            print("Usage: attack <name> [with <weapon>]")
            return
        name = parts[0]
        weapon = "sword" if len(parts) < 2 else parts[1]
        response = self.send_command(f"attack {name} {weapon}")
        if response == "no_monster":
            print(f"No {name} here")
        else:
            print(response)

    def do_quit(self, arg):
        "Exit the game."
        print("Goodbye!")
        self.s.close()
        return True

    def do_exit(self, arg):
        "Exit the game."
        return self.do_quit(arg)

if __name__ == "__main__":
    print("<<< Welcome to Python-MUD 0.1 >>>")
    Client_MUD().cmdloop()


import socket
import cowsay
import cmd
import shlex
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
    promt = 'MUD> '
    host = "localhost"
    port = 12345

   def __init__(self):
        super().__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))

    def send_command(self, command):
        self.s.sendall(command.encode())
        return self.s.recv(1024).decode()

    def move(self, arg):
        "Move the player: move <direction>"
        directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
        if arg not in directions:
            print("Invalid direction. Use 'up', 'down', 'left', or 'right'.")
            return
        dx, dy = directions[arg]
        response = self.send_command(f"move {dx} {dy}")
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


    def addmon(self, name, x, y, hello, hp):
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

    def attack(self, name, weapon):
        "Attack a monster: attack <name> [with <weapon>]"
        parts = shlex.split(arg)
        if not parts:
            print("Usage: attack <name> [with <weapon>]")
            return
        name = parts[0]
        weapon = "sword" if len(parts) < 2 else parts[1]
        damage = 10 if weapon == "sword" else 15 if weapon == "spear" else 20
        response = self.send_command(f"attack {name} {damage}")
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

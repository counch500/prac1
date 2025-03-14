import sys
import cowsay
import shlex
import cmd

GRID_SIZE = 10

class MudGame(cmd.Cmd):
    prompt = "(mud) "

    def __init__(self):
        super().__init__()
        self.player_position = [0, 0]
        self.monsters = {}
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
        self.field_size = GRID_SIZE
    def move_player(self, direction):
        x, y = self.player_position
        if direction == "up":
            y = y - 1 if y > 0 else GRID_SIZE - 1
        elif direction == "down":
            y = y + 1 if y < GRID_SIZE - 1 else 0
        elif direction == "left":
            x = x - 1 if x > 0 else GRID_SIZE - 1
        elif direction == "right":
            x = x + 1 if x < GRID_SIZE - 1 else 0
        else:
            print("Invalid command")
            return

        self.player_position[0], self.player_position[1] = x, y
        print(f"Moved to ({x}, {y})")
        if (x, y) in self.monsters:
            self.encounter(x, y)

    def add_custom_monster(self, hello,x, y, hitpoints):
        jgsbat = """               ,_                    _, 
               ) '-._  ,_    _,  _.-' (
               )  _.-'.|\\--//|.'-._  (
                )'   .'\/o\/o\/'.   (
                 ) .' . \====/ . '. (
                  )  / <<    >> \  (
                   '-._/`  \_.-'
             jgs     __\\'--'//__
                    (((""  ""))) """
        print(jgsbat)
        print(hello)
        name = "jgsbat"
        self.monsters[(x, y)] = (name, hello, hitpoints)
        print(f"Custom monster {name} added at ({x}, {y}) saying {hello} with {hitpoints} hitpoints")
    def add_monster(self, name, x, y, hello, hitpoints):
        if name == "jgsbat":
            self.add_custom_monster(hello)
            return

        if name not in cowsay.list_cows() and name != "jgsbat" and name != "cow":
            print(f"Cannot add unknown monster: {name}")
            return

        try:
            x, y = int(x), int(y)
            if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
                raise ValueError
        except ValueError:
            print("Invalid coordinates")
            return

        replaced = (x, y) in self.monsters
        self.monsters[(x, y)] = (name, hello, hitpoints)

        print(f"Added monster {name} at ({x}, {y}) saying {hello} with {hitpoints} hitpoints")

        if replaced:
            print("Replaced the old monster")

    def encounter(self, x, y):
        if (x, y) not in self.monsters:
            print("No monster here")
            return

        name, hello, hitpoints = self.monsters[(x, y)]

        if name == "jgsbat":
            self.add_custom_monster(hello, x, y, hitpoints)
        else:
            print(cowsay.cowsay(hello, cow=name))

    def do_move(self, arg):
        "Move the player in a direction: move <up|down|left|right>"
        self.move_player(arg)

    def complete_move(self, text, line, begidx, endidx):
        return [d for d in ["up", "down", "left", "right"] if d.startswith(text)]

    def do_addmon(self, arg):
        "Add a monster: addmon <name> coords <x> <y> hello <message> hp <hitpoints>"
        usage = "Usage: addmon <NAME> hello <MESSAGE> hp <HP> coords <X> <Y>"
        args = shlex.split(arg)
        if len(args) < 7:
            print("Invalid arguments\n{usage}")
            return
        name, hello, hp, x, y = None, None, None, None, None
        try:
            name = args[0]
            hello = args[args.index('hello') + 1]
            hp = int(args[args.index('hp') + 1])
            x, y = int(args[args.index('coords') + 1]), int(args[args.index('coords') + 2])

            if not (0 <= x < self.field_size and 0 <= y < self.field_size):
                print(f"Invalid coordinates\nField size is {self.field_size}x{self.field_size}")
                return

            if hp <= 0:
                print("Hitpoints should be a positive integer.")
                return
            
            if (x, y) in self.monsters:
                print(f"Replaced the old monster at ({x}, {y})")
            
            self.monsters[(x, y)] = (name, hello, hp)
            print(f"Added monster {name} at ({x}, {y}) saying {hello} with {hp} HP")

        except (ValueError, IndexError) as e:
            print(f"Error: {e}\n{usage}")

    def do_attack(self, arg):
        "Attack a monster: attack [with <weapon>]"
        parts = shlex.split(arg)
        if not parts:
            print("Usage: attack <monster_name>")
            return
        monster_name = parts[0]
        weapon = "sword" if len(parts) < 2 else parts[1]

        if weapon not in self.weapons:
            print("Unknown weapon")
            return

        x, y = self.player_position
        for (mx, my), (name, hello, hp) in self.monsters.items():
            if name == monster_name and (mx, my) == (x, y):
                damage = min(10, hp)
                hp -= damage
                print(f"Attacked {name}, damage {damage} hp")
                if hp <= 0:
                    print(f"{name} died")
                    del self.monsters[(mx, my)]
                else:
                    print(f"{name} now has {hp} hp")
                    self.monsters[(mx, my)] = (name, hello, hp)

    def complete_attack(self, text, line, begidx, endidx):
        parts = shlex.split(line[:begidx])
        if len(parts) ==1:
            return [m for (x, y), (m, h, hp) in self.monsters.items() if m.startswith(text)]
        elif len(parts) == 2 and parts[-1] == "with":
            return [w for w in self.weapons if w.startswith(text)]
        return []

if __name__ == "__main__":
    print("<<< Welcome to Python-MUD 0.1 >>>")
    MudGame().cmdloop()


import sys
import cowsay
import shlex

GRID_SIZE = 10

class MudGame(cmd.Cmd):
    prompt = "(mud) "

    def __init__(self):
        super().__init__()
        player_position = [0, 0]
        monsters = {}
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
    def move_player(self, direction):
        x, y = self.player_position
        if direction == "up":
            y = (y - 1) % GRID_SIZE
        elif direction == "down":
            y = (y + 1) % GRID_SIZE
        elif direction == "left":
            x = (x - 1) % GRID_SIZE
        elif direction == "right":
            x = (x + 1) % GRID_SIZE
        else:
            print("Invalid command")
            return
        self.player_position[0], self.player_position[1] = x, y
        print(f"Moved to ({x}, {y})")
        if (x, y) in self.monsters:
            self.encounter(x, y)

    def add_custom_monster(self, hello):
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
        name, hello, hitpoints = self.monsters[(x, y)]
        print(cowsay.cowsay(hello, cow=name))

    def do_move(self, arg):
        "Move the player in a direction: move <up|down|left|right>"
        self.move_player(arg)

    def complete_move(self, text, line, begidx, endidx):
        return [d for d in ["up", "down", "left", "right"] if d.startswith(text)]

    def do_addmon(self, arg):
        "Add a monster: addmon <name> coords <x> <y> hello <message> hp <hitpoints>"
        parts = shlex.split(arg)
        if len(parts) < 9:
            print("Invalid addmon command")
            return
        if 'hello' in parts and 'hp' in parts and 'coords' in parts:
            hello_index = parts.index('hello') + 1
            hp_index = parts.index('hp') + 1
            coords_index = parts.index('coords') + 1

            hello_string = parts[hello_index]
            hitpoints = parts[hp_index]
            x_coord = parts[coords_index]
            y_coord = parts[coords_index + 1]

            try:
                hitpoints = int(hitpoints)
                if hitpoints <= 0:
                    print("Invalid hitpoints value")
                    return
            except ValueError:
                print("Hitpoints should be a positive integer")
                return

            self.add_monster(parts[1], x_coord, y_coord, hello_string, hitpoints)

        else:
            print("Invalid addmon command")

    def do_attack(self, arg):
        "Attack a monster: attack [with <weapon>]"
        parts = shlex.split(arg)
        weapon = "sword" if len(parts) < 2 else parts[1]

        if weapon not in self.weapons:
            print("Unknown weapon")
            return

        x, y = self.player_position
        if (x, y) not in self.monsters:
            print("No monster here")
            return

        name, hello, hp = self.monsters[(x, y)]
        damage = min(self.weapons[weapon], hp)
        hp -= damage
        print(f"Attacked {name} with {weapon}, damage {damage} hp")

        if hp <= 0:
            print(f"{name} died")
            del self.monsters[(x, y)]
        else:
            print(f"{name} now has {hp} hp")
            self.monsters[(x, y)] = (name, hello, hp)

    def complete_attack(self, text, line, begidx, endidx):
        parts = shlex.split(line[:begidx])
        if len(parts) == 1:
            return [w for w in self.weapons if w.startswith(text)]
        return []


if __name__ == "__main__":
    print("<<< Welcome to Python-MUD 0.1 >>>")
    MudGame().cmdloop()


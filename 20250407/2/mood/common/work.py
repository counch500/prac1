"""
Common utilities for MOOD MUD game.
"""

import cmd
import shlex
import cowsay
import sys

class MUD(cmd.Cmd):
    prompt = ">"
    weapons = {"sword": 10, "spear": 15, "axe": 20}

    def __init__(self):
        self.completekey = "tab"
        self.cmdqueue = []
        self.field = [[None for _ in range(10)] for _ in range(10)]
        self.player_position = (0, 0)
        print("<<< Welcome to Python-MUD 0.1 >>>")

        self.jgsbat_func = None
        try:
            with open("jgsbat.cow", "r", encoding="utf-8") as f:
                jgsbat_template = cowsay.read_dot_cow(f)  # шаблон ackii-арта
                self.jgsbat_func = lambda msg: cowsay.cowsay(msg, cowfile=jgsbat_template)
        except Exception as e:
            print(f"Ошибка загрузки монстра jgsbat: {e}")

    def do_up(self, arg):
        """Двигает игрока вверх"""
        self.move_player("up")

    def do_down(self, arg):
        """Двигает игрока вниз"""
        self.move_player("down")

    def do_left(self, arg):
        """Двигает игрока влево"""
        self.move_player("left")

    def do_right(self, arg):
        """Двигает игрока вправо"""
        self.move_player("right")

   def do_quit(self, arg):
        """Выйти из игры: quit"""
        print("Выход из игры...")
        self.socket.close()
        sys.exit(1)

    def move_player(self, direction):
        x, y = self.player_position
        if direction == 'up':
            y = (y - 1) % 10
        elif direction == 'down':
            y = (y + 1) % 10
        elif direction == 'left':
            x = (x - 1) % 10
        elif direction == 'right':
            x = (x + 1) % 10
        else:
            print("Invalid command")
            return

        self.player_position = (x, y)
        print(f"Moved to ({x}, {y})")
        self.encounter(x, y)

    def do_attack(self, arg):
        """Атаковать монстра в текущей позиции"""
        parts = arg.split()
        if len(parts) == 0:
            print("attack name witn weapon")
            return
        if len(parts) == 3 and parts[1] == "with":
            monster_name, weapon = parts[0], parts[2]
        elif len(parts) == 1:
            monster_name, weapon = parts[0], "sword"
        else:
            print("Usage: attack <monster_name> with <weapon>")
            return
        if weapon not in self.weapons:
            print("Unknown weapon")
            return
        x, y = self.player_position
        monster = self.field[x][y]
        if not monster or monster[0] != monster_name:
            print(f"No {monster_name} here")
            return
        name, hello, hp = monster
        damage = min(self.weapons[weapon], hp)
        hp -= damage
        print(f"Attacked {name} with {weapon}, damage {damage} hp")
        if hp <= 0:
            print(f"{name} died")
            self.field[x][y] = None 
        else:
            print(f"{name} now has {hp} hp")
            self.field[x][y] = (name, hello, hp)

    def complete_attack(self, text, line, begidx, endidx):
        """Автодополнение attack по именам доступных монстров"""
        words = shlex.split(line[:endidx], posix=False)
    # Разбиваем строку с учетом пробелов в кавычках
        raw_words = line[:endidx].split()

        if len(words) == 1 and not line.endswith(' '):
            return [m for m in self.monster_list if m.startswith(text)]
        # Автодополнение имени монстра
        if len(words) == 2:
            return [m for m in self.monster_list if m.startswith(text)]
                
        if (len(words) == 1 and line.endswith(' ')) or (len(words) == 2 and not line.endswith(' ')):
            return [m for m in self.monster_list if m.startswith(text)]
        # Автодополнение ключевого слова 'with'
        if len(words) == 3 and words[-1] == "with" and not line.endswith(' '):
            return []
    
    # Если ввели "attack монстр with " (пробел после with)
        if (len(raw_words) >= 3 and raw_words[-2] == "with" and line.endswith(' ')) or \
            (len(words) == 3 and line.endswith('with ')):
            return self.weapons
        elif len(words) == 3 and not line.endswith(' '):
            return ['with'] if 'with'.startswith(text) else []
        
        # Автодополнение оружия после 'with'
        elif len(words) >= 4 and words[-2] == 'with':
            return [w for w in self.weapons if w.startswith(text)]
        return []
    def do_addmon(self, arg):
        """Добавляет монстра. Использование: addmon <name> hello <msg> hp <hp> coords <x> <y>"""
        try:
            parts = shlex.split(arg)
            if len(parts) < 7:
                raise ValueError("not enough arguments for addmon")

            name = parts[0]
            args = {}
            key = None
            for part in parts[1:]:
                if part in ["hello", "hp", "coords"]:
                    key = part
                elif key is not None:
                    args[key] = part if key not in args else args[key] + " " + part
            if not all(k in args for k in ["hello", "hp", "coords"]):
                raise ValueError("missing required arguments")

            hello = args["hello"]
            hp = int(args["hp"])
            x, y = map(int, args["coords"].split())

            if hp <= 0:
                print("hitpoints must be positive")
                return

            self.add_monster(name, x, y, hello, hp)
        except (ValueError, KeyError):
            print("Invalid arguments")

    def add_monster(self, name, x, y, hello, hp):
        if name not in cowsay.list_cows() and name != "jgsbat":
            print("cannot add unknown monster")
            return
        if (x, y) == self.player_position:
            print("cannot add monster to player's position")
            return

        old_mon = self.field[x][y] is not None
        self.field[x][y] = (name, hello, hp)
        print(f"Added monster {name} to ({x}, {y}) saying {hello} with {hp} hitpoints")

        if old_mon:
            print("Replaced the old monster")

    def encounter(self, x, y):
        monster = self.field[x][y]
        if monster is not None:
            name, hello, _ = monster
            if name == "jgsbat" and self.jgsbat_func:
                print(self.jgsbat_func(hello))  
            else:
                print(cowsay.cowsay(hello, cow=name))

    def complete_addmon(self, text, line, begidx, endidx):
        words = shlex.split(line[:endidx])
    
    # Если только "addmon" и начали вводить (не завершили пробелом)
        if len(words) == 1 and not line.endswith(' '):
            return [c for c in self.monster_list if c.startswith(text)]
    
    # Если вводим название монстра (первый аргумент)
        if (len(words) == 1 and line.endswith(' ')) or (len(words) == 2 and not line.endswith(' ')):
            return [m for m in self.monster_list if m.startswith(text)]
    
    # Автодополнение параметров (hello, hp, coords)
        if len(words) >= 2 and words[-1] not in ['hello', 'hp', 'coords']:
            options = ['hello', 'hp', 'coords']
            return [o for o in options if o.startswith(text)]
    
    # Автодополнение значений параметров
        if len(words) >= 3:
            if words[-2] == 'coords' and len(words[-1]) < 2:
                return [str(i) for i in range(10) if str(i).startswith(text)]
            elif words[-2] == 'hp':
                return [str(i) for i in range(1, 100) if str(i).startswith(text)]
            elif words[-2] == 'hello':
                return ['"Hello!"' if '"Hello!"'.startswith(text) else text]
        return []

    def do_EOF():
        return 1


if __name__ == "__main__":
    game = MUD()
    game.cmdloop()
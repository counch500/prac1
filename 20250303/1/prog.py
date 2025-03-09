import sys
import cowsay
import shlex

GRID_SIZE = 10

player_position = [0, 0]
monsters = {}

def move_player(direction):
    x, y = player_position
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
    player_position[0], player_position[1] = x, y
    print(f"Moved to ({x}, {y})")
    if (x, y) in monsters:
        encounter(x, y)

def add_custom_monster(hello):
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

def add_monster(name, x, y, hello, hitpoints):
    if name == "jgsbat":
        add_custom_monster(hello)
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

    replaced = (x, y) in monsters
    monsters[(x, y)] = (name, hello, hitpoints)

    print(f"Added monster {name} at ({x}, {y}) saying {hello} with {hitpoints} hitpoints")

    if replaced:
        print("Replaced the old monster")

def encounter(x, y):
    name, hello, hitpoints = monsters[(x, y)]
    print(cowsay.cowsay(hello, cow=name))

def process_command(command):
    parts = shlex.split(command.strip())
    if not parts:
        return
    
    if parts[0] in {"up", "down", "left", "right"}:
        move_player(parts[0])

    elif parts[0] == "addmon" and len(parts) >= 9:
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

            add_monster(parts[1], x_coord, y_coord, hello_string, hitpoints)

        else:
            print("Invalid addmon command")
    else:
        print("Invalid command")

def main():
    print("<<< Welcome to Python-MUD 0.1 >>>")
    for line in sys.stdin:
        process_command(line)

main()


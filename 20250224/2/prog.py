import sys
import cowsay

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

def add_monster(name, x, y, hello):
    if name not in cowsay.list_cows():
        print("Cannot add unknown monster")
        return

    try:
        x, y = int(x), int(y)
        if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
            raise ValueError
    except ValueError:
        print("Invalid arguments")
        return
    replaced = (x, y) in monsters
    monsters[(x, y)] = (name, hello)
    print(f"Added monster {name} to ({x}, {y}) saying {hello}")
    if replaced:
        print("Replaced the old monster")

def encounter(x, y):
    name, hello = monsters[(x, y)]
    print(cowsay.cowsay(hello, cow=name))

def process_command(command):
    parts = command.strip().split()
    if not parts:
        return
    if parts[0] in {"up", "down", "left", "right"}:
        move_player(parts[0])
    elif parts[0] == "addmon" and len(parts) == 5:
        add_monster(parts[1], parts[2], parts[3], parts[4])
    else:
        print("Invalid command")

def main():
    for line in sys.stdin:
        process_command(line)

main()


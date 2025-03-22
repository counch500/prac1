import asyncio

GRID_SIZE = 10

class MudServer:
    def __init__(self):
        self.player_position = [0, 0]
        self.monsters = {}
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
        self.available_monsters = ["jgsbat", "cow", "dragon", "goblin"]

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
            return "Invalid direction"

        self.player_position = [x, y]
        if (x, y) in self.monsters:
            name, hello, hp = self.monsters[(x, y)]
            return f"moved {x} {y}\nencounter {name} {hello}"
        return f"moved {x} {y}"

    def add_monster(self, name, x, y, hello, hp):
        if name not in self.available_monsters:
            return "Cannot add unknown monster"
        if (x, y) in self.monsters:
            self.monsters[(x, y)] = (name, hello, hp)
            return f"added {name} {x} {y} {hello} {hp}\nReplaced the old monster"
        self.monsters[(x, y)] = (name, hello, hp)
        return f"added {name} {x} {y} {hello} {hp}"

    def attack_monster(self, name, weapon):
        x, y = self.player_position
        if (x, y) not in self.monsters or self.monsters[(x, y)][0] != name:
            return "no_monster"
        damage = self.weapons.get(weapon, 10)
        _, hello, hp = self.monsters[(x, y)]
        hp -= damage
        if hp <= 0:
            del self.monsters[(x, y)]
            return f"attacked {name} {damage} 0\n{name} died"
        self.monsters[(x, y)] = (name, hello, hp)
        return f"attacked {name} {damage} {hp}"

async def handle_client(reader, writer):
    game = MudServer()
    print("New client connected")

    while True:
        data = await reader.read(100)
        if not data:
            print("Client disconnected")
            break

        command = data.decode().strip()
        print(f"Received: {command}")

        parts = command.split()
        if not parts:
            response = "Invalid command"
        elif parts[0] == "move":
            direction = parts[1]
            print(f"Moving player: {direction}")
            response = game.move_player(direction)
        elif parts[0] == "addmon":
            name, x, y, hello, hp = parts[1], int(parts[2]), int(parts[3]), parts[4], int(parts[5])
            print(f"Adding monster: {name} at ({x}, {y})")
            response = game.add_monster(name, x, y, hello, hp)
        elif parts[0] == "attack":
            name, weapon = parts[1], parts[2]
            print(f"Attacking {name} with {weapon}")
            response = game.attack_monster(name, weapon)
        else:
            response = "Invalid command"

        print(f"Sending: {response}")
        writer.write(response.encode())
        await writer.drain()

    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 12345)
    print("Server started on localhost:12345")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())


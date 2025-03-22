import asyncio

GRID_SIZE = 10

class MudGame:
    def __init__(self):
        self.player_position = [0, 0]
        self.monsters = {}
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}


    def move_player(self, dx, dy):
        x, y = self.player_position
        x = (x + dx) % GRID_SIZE
        y = (y + dy) % GRID_SIZE
        self.player_position = [x, y]
        if (x, y) in self.monsters:
            name, hello, hp = self.monsters[(x, y)]
            return f"moved {x} {y}\nencounter {name} {hello}"
        return f"moved {x} {y}"

    def add_monster(self, name, x, y, hello, hp):
        if (x, y) in self.monsters:
            self.monsters[(x, y)] = (name, hello, hp)
            return f"added {name} {x} {y} {hello} {hp}\nReplaced the old monster"
        self.monsters[(x, y)] = (name, hello, hp)
        return f"added {name} {x} {y} {hello} {hp}"

    def attack_monster(self, name, weapon):
        x, y = self.player_position
        if (x, y) not in self.monsters or self.monsters[(x, y)][0] != name:
            return f"No {name} here"
        damage = self.weapons.get(weapon, 10)
        _, hello, hp = self.monsters[(x, y)]
        hp -= damage
        if hp <= 0:
            del self.monsters[(x, y)]
            return f"Attacked {name}, damage {damage} hp\n{name} died"
        self.monsters[(x, y)] = (name, hello, hp)
        return f"Attacked {name}, damage {damage} hp\n{name} now has {hp} hp"

async def handle_client(reader, writer):
    game = MudGame()

    while True:
        data = await reader.readline()
        if not data:
            break

        command = data.decode().strip()
        parts = command.split()
        if not parts:
            response = "Invalid command"

        elif parts[0] == "move":
            dx, dy = map(int, parts[1:])
            response = game.move_player(dx, dy)

        elif parts[0] == "addmon":
            name, x, y, hello, hp = parts[1], int(parts[2]), int(parts[3]), parts[4], int(parts[5])
            response = game.add_monster(name, x, y, hello, hp)
        elif parts[0] == "attack":
            name, damage = parts[1], int(parts[2])
            response = game.attack_monster(name, damage)
        else:
            response = "Invalid command"

        writer.write(response.encode())
        await writer.drain()

    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 12345)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())

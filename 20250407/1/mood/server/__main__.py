"""
Server module for MOOD MUD game.
"""

import asyncio
import cowsay
import shlex


clients = {}  
games = {}  

# Глобальные переменные для хранения общего состояния игры
game_field = [[None for _ in range(10)] for _ in range(10)]
monsters = set()


class MUD:
    def __init__(self, username):
        self.player_position = (0, 0)
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
        self.username = username
        self.jgsbat_func = None
        try:
            with open("jgsbat.cow", "r", encoding="utf-8") as f:
                jgsbat_template = cowsay.read_dot_cow(f)
                self.jgsbat_func = lambda msg: cowsay.cowsay(msg, cowfile=jgsbat_template)
        except Exception as e:
            print(f"Ошибка загрузки монстра jgsbat: {e}")

    def move_player(self, d_x, d_y):
        x, y = self.player_position
        x = (x + d_x) % 10
        y = (y + d_y) % 10
        self.player_position = (x, y)
        return f"{x} {y}"

    def encounter(self, x, y):
        monster = game_field[x][y]
        if monster:
            name, hello, _ = monster
            if name == "jgsbat" and self.jgsbat_func:
                return self.jgsbat_func(hello)
            return cowsay.cowsay(hello, cow=name)
        return ''

    def moving(self, d_x, d_y):
        new_position = self.move_player(d_x, d_y)
        encounter_message = self.encounter(self.player_position[0], self.player_position[1])
        if encounter_message:
            return f"Moved to ({new_position})\n{encounter_message}"
        return f"Moved to ({new_position})"

    def add_monster(self, x, y, hp, hello, name):
        if name not in cowsay.list_cows() and name != "jgsbat":
            return "cannot add unknown monster"
        if (x, y) == self.player_position:
            return "cannot add monster to player's position"

        old_mon = game_field[x][y] is not None
        game_field[x][y] = (name, hello, hp)
        monsters.add(name)
        return "1" if old_mon else "0"

    def attack(self, weapon, name):
        if name not in monsters:
            return f'no such monster {name}'
        x, y = self.player_position
        monster = game_field[x][y]
        if not monster or monster[0] != name:
            return f'no {name} here'
        name, hello, hp = monster
        damage = min(self.weapons[weapon], hp)
        hp -= damage
        if hp <= 0:
            game_field[x][y] = None
            monsters.remove(name)
            return f'{damage} 0'
        game_field[x][y] = (name, hello, hp)
        return f'{damage} {hp}'


async def broadcast_message(message, exclude=None):
    for username, queue in clients.items():
        if username != exclude:
            await queue.put(message)


async def handle_client(reader, writer):
    username = (await reader.readline()).decode().strip()

    if username in clients:
        writer.write(b"Username already taken\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    clients[username] = asyncio.Queue()
    games[username] = MUD(username)

    writer.write(b"Welcome to MUD!\n")
    await writer.drain()

    await broadcast_message(f"[SERVER] {username} has joined the game", exclude=username)
    print(f"[SERVER] {username} connected")

    send_task = asyncio.create_task(send_messages(writer, username))

    try:
        while not reader.at_eof():
            data = await reader.readline()
            if not data:
                break

            message = data.decode().strip()
            parts = message.split()
            if not parts:
                continue

            cmd = parts[0]
            game = games[username]

            if cmd == "addmon":
                try:
                    name, x, y, hp = parts[1:5]
                    hello = ' '.join(parts[5:])
                    x, y, hp = map(int, [x, y, hp])
                    if name not in cowsay.list_cows() and name != "jgsbat":
                        await clients[username].put("cannot add unknown monster")
                        continue
                    if (x, y) == game.player_position:
                        await clients[username].put("cannot add the monster in player's position")
                        continue
                    if x < 0 or x >= 10 or y < 0 or y >= 10 or hp <= 0:
                        await clients[username].put("Invalid arguments")
                        continue

                    old_mon = game_field[x][y] is not None
                    game_field[x][y] = (name, hello, hp)
                    monsters.add(name)
                    message = f"[SERVER]{username} added monster {name} to ({x}, {y}) with {hp} hp"
                    if old_mon:
                        message += "\nReplaced the old monster"
                    await broadcast_message(message)
                except (ValueError, IndexError):
                    await clients[username].put("Invalid arguments")

            elif cmd == "attack":
                try:
                    weapon, name = parts[1:3]
                    if weapon not in ["sword", "spear", "axe"]:
                        await clients[username].put("Unknown weapon")
                        continue
                    if name not in monsters:
                        await clients[username].put(f"no such monster {name}")
                        continue

                    x, y = game.player_position
                    monster = game_field[x][y]
                    if not monster or monster[0] != name:
                        await clients[username].put(f"no {name} here")
                        continue

                    name, hello, hp = monster
                    damage = min(game.weapons[weapon], hp)
                    hp -= damage
                    if hp <= 0:
                        game_field[x][y] = None
                        monsters.remove(name)
                        print(f"[SERVER] {username} убил {name} в ({x},{y})")
                        await broadcast_message(f"{username} attacked {name} with {weapon} for {damage} hp, {name} died")
                    else:
                        game_field[x][y] = (name, hello, hp)
                        await broadcast_message(f"[SERVER] {username} attacked {name} with {weapon} for {damage} hp, {name} has {hp} hp left")
                except (ValueError, IndexError):
                    await clients[username].put("Invalid arguments")

            elif cmd == "move":
                try:
                    d_x, d_y = map(int, parts[1:3])
                    new_position = game.move_player(d_x, d_y)
                    encounter_message = game.encounter(game.player_position[0], game.player_position[1])
                    if encounter_message:
                        await clients[username].put(f"[SERVER] Moved to ({new_position})\n{encounter_message}")
                    else:
                        await clients[username].put(f"[SERVER] Moved to ({new_position})")
                except (ValueError, IndexError):
                    await clients[username].put("Invalid arguments")

            elif cmd == "sayall":
                if len(parts) < 2:
                    await clients[username].put("Invalid arguments")
                    continue
                try:
                    parsed = shlex.split(message)
                    if len(parsed) < 2:
                        await clients[username].put("Invalid arguments")
                        continue
                    msg_to_broadcast = ' '.join(parsed[1:])
                    await broadcast_message(f"[SERVER] {username}: {msg_to_broadcast}")
                except ValueError:
                    await clients[username].put("Invalid arguments")

            else:
                await clients[username].put("Unknown command")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        send_task.cancel()
        try:
            await send_task
        except asyncio.CancelledError:
            pass

        if username in clients:
            del clients[username]
        if username in games:
            del games[username]

        await broadcast_message(f"[SERVER] {username} has left the game", exclude=username)

        writer.close()
        await writer.wait_closed()
        print(f"{username} disconnected")


async def send_messages(writer, username):
    try:
        while True:
            message = await clients[username].get()
            writer.write(message.encode() + b'\n')
            await writer.drain()
    except asyncio.CancelledError:
        pass


async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 1337)
    addr = server.sockets[0].getsockname()
    print(f"[SERVER] Запущен на {addr[0]}:{addr[1]}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
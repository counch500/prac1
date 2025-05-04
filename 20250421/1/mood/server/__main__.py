"""
Server module for MOOD MUD game with full localization support matching reference implementation.
"""

import random
import asyncio
import cowsay
import shlex
import gettext
import os
from pathlib import Path

class MUD:
    """Main MUD game class with localized messages matching reference implementation."""
    try:
        locales_dir = os.path.join(os.path.dirname(__file__), 'locales')
        LOCALES = {
            "ru_RU.UTF-8": gettext.translation(
                'mood',
                locales_dir,
                languages=['ru'],
                fallback=True
            ),
            "en_US.UTF-8": gettext.NullTranslations(),
        }
    except Exception as e:
        print(f"Failed to load translations: {e}")
        LOCALES = {
            "ru_RU.UTF-8": gettext.NullTranslations(),
            "en_US.UTF-8": gettext.NullTranslations(),
        }

    def __init__(self, username):
        self.player_position = (0, 0)
        self.weapons = {
            "sword": 10, 
            "spear": 15, 
            "axe": 20
        }
        self.username = username
        self.locale = 'en_US.UTF-8'
        self.jgsbat_func = None
        
        try:
            with open("jgsbat.cow", "r", encoding="utf-8") as f:
                jgsbat_template = cowsay.read_dot_cow(f)
                self.jgsbat_func = lambda msg: cowsay.cowsay(msg, cowfile=jgsbat_template)
        except Exception as e:
            print(self._("Failed to add jgsbat: {error}", self.locale).format(error=e))

    def _(self, text, locale=None):
        locale = locale or self.locale
        return self.LOCALES[locale].gettext(text)

    def ngettext(self, text, ntext, n, locale=None):
        locale = locale or self.locale
        return self.LOCALES[locale].ngettext(text, ntext, n)

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

clients = {}
games = {}
game_field = [[None for _ in range(10)] for _ in range(10)]
monsters = set()
wandering_monsters_enabled = True

async def send_localized(queue, locale, msg, *args):
    """Send properly localized message to client queue"""
    try:
        game = games[next(username for username, q in clients.items() if q == queue)]
        if any(isinstance(arg, int) for arg in args):
            last_num = next(arg for arg in reversed(args) if isinstance(arg, int))
            localized = game.ngettext(msg, msg.replace("hp", "hps"), last_num, locale).format(*args)
        else:
            localized = game._(msg, locale).format(*args)
        await queue.put(localized)
    except Exception as e:
        print(f"Localization error: {e}")
        await queue.put(msg % args)  # Fallback

async def broadcast_localized(msg, *args, exclude=None):
    """Broadcast message localized for each client"""
    for username, queue in clients.items():
        if username != exclude:
            game = games[username]
            if any(isinstance(arg, int) for arg in args):
                last_num = next(arg for arg in reversed(args) if isinstance(arg, int))
                localized = game.ngettext(msg, msg.replace("hp", "hps"), last_num).format(*args)
            else:
                localized = game._(msg).format(*args)
            await queue.put(localized)

async def handle_client(reader, writer):
    """Handle client connection with full localization support matching reference"""
    username = (await reader.readline()).decode().strip()

    if username in clients:
        game = MUD('temp')
        writer.write(game._("Username already taken\n", 'en_US.UTF-8').encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    clients[username] = asyncio.Queue()
    games[username] = MUD(username)

    welcome_msg = games[username]._("Welcome to MUD, {}!\n").format(username)
    writer.write(welcome_msg.encode())
    await writer.drain()

    await broadcast_localized("{} connected to raid!\n", username, exclude=username)

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

            if cmd == "locale":
                if len(parts) < 2:
                    await clients[username].put(game._("Usage: locale <lang>\n"))
                    continue
                
                lang = parts[1]
                if lang not in game.LOCALES:
                    await clients[username].put(
                        game._("Only ru_RU.UTF-8 and en_US.UTF-8 locales are available\n"))
                    continue
                
                game.locale = lang
                await clients[username].put(
                    game._("Set up locale: {}\n").format(lang))

            elif cmd == "addmon":
                try:
                    name, x, y, hp = parts[1:5]
                    hello = ' '.join(parts[5:])
                    x, y, hp = map(int, [x, y, hp])
                    
                    if name not in cowsay.list_cows() and name != "jgsbat":
                        await clients[username].put(_("Cannot add unknown monster"))
                        continue
                    if (x, y) == game.player_position:
                        await clients[username].put(_("Cannot add monster to player's position"))
                        continue
                    if x < 0 or x >= 10 or y < 0 or y >= 10 or hp <= 0:
                        await clients[username].put(_("Invalid arguments"))
                        continue

                    old_mon = game_field[x][y] is not None
                    game_field[x][y] = (name, hello, hp)
                    monsters.add(name)
                    
                    await broadcast_localized(
                        game.ngettext(
                            "{} added monster {} to ({}, {}) with {} hp",
                            "{} added monster {} to ({}, {}) with {} hp", 
                            hp
                        ).format(
                            username,
                            name,
                            x,
                            y,
                            hp
                        ),
                        exclude=username
                    )
                    if old_mon:
                        await broadcast_localized(game._("Replaced the old monster\n"))
                except (ValueError, IndexError):
                    await clients[username].put(game._("Invalid arguments"))
            elif cmd == "attack":
                """Handle attack command: attack <weapon> <monster_name>"""
                try:
                    weapon, name = parts[1:3]
                    if weapon not in game.weapons:
                        await clients[username].put(game._("Unknown weapon\n"))
                        continue

                    if name not in monsters:
                        await clients[username].put(game._("No such monster {}\n").format(name))
                        continue

                    x, y = game.player_position
                    monster = game_field[x][y]
                    if not monster or monster[0] != name:
                        await clients[username].put(game._("No {} here\n").format(name))
                        continue

                    name, hello, hp = monster
                    damage = min(game.weapons[weapon], hp)
                    hp -= damage

                    if hp <= 0:
                        game_field[x][y] = None
                        monsters.remove(name)
                        await broadcast_localized(
                            game.ngettext(
                                "{} attacked {} with {} for {} hp, {} died",
                                "{} attacked {} with {} for {} hp, {} died", 
                                damage
                            ).format(
                                username,
                                name,
                                weapon,
                                damage,
                                name
                            ),
                            exclude=username
                        )
                    else:
                        game_field[x][y] = (name, hello, hp)
                        await broadcast_localized(
                            game.ngettext(
                                "{} attacked {} with {} for {} hp, {} has {} hp left",
                                "{} attacked {} with {} for {} hp, {} has {} hp left", 
                                hp
                            ).format(
                                username,
                                name,
                                weapon,
                                damage,
                                name,
                                hp
                            ),
                            exclude=username
                        )
                except (ValueError, IndexError):
                    await clients[username].put(game._("Invalid arguments\n"))


            elif cmd == "move":
                """Handle move command: move dx dy"""
                try:
                    d_x, d_y = map(int, parts[1:3])
                    new_position = game.move_player(d_x, d_y)
                    encounter_message = game.encounter(game.player_position[0], game.player_position[1])
                    if encounter_message:
                        await clients[username].put(
                            game._("[SERVER] Moved to ({})\n{}").format(new_position, encounter_message)
                        )
                    else:
                        await clients[username].put(
                            game._("[SERVER] Moved to ({})").format(new_position)
                        )
                except (ValueError, IndexError):
                    await clients[username].put(
                        game._("Invalid arguments")
                    )

            elif cmd == "sayall":
                """Handle sayall command: sayall message"""
                if len(parts) < 2:
                    await clients[username].put(
                        game._("Invalid arguments")
                    )
                    continue
                try:
                    parsed = shlex.split(message)
                    if len(parsed) < 2:
                        await clients[username].put(
                            game._("Invalid arguments")
                        )
                        continue
                    msg_to_broadcast = ' '.join(parsed[1:])
                    await broadcast_localized(
                        "[SERVER] {}: {}",
                        username, msg_to_broadcast
                    )
                except ValueError:
                    await clients[username].put(
                        game._("Invalid arguments")
                    )
            elif cmd == "movemonsters":
                try:
                    global wandering_monsters_enabled
                    state = parts[1].lower()
                    if state == "on":
                        if not wandering_monsters_enabled:
                            wandering_monsters_enabled = True
                            await broadcast_localized("Moving monsters: on")
                        else:
                            await clients[username].put(_("Moving monsters: on", game.locale))
                    elif state == "off":
                        if wandering_monsters_enabled:
                            wandering_monsters_enabled = False
                            await broadcast_localized("Moving monsters: off")
                        else:
                            await clients[username].put(_("Moving monsters: off", game.locale))
                    else:
                        await clients[username].put(_("Invalid argument. Use 'on' or 'off'", game.locale))
                except IndexError:
                    await clients[username].put(_("Invalid arguments. Usage: movemonsters on|off", game.locale))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        send_task.cancel()
        try:
            await send_task
        except asyncio.CancelledError:
            pass

        game = games.get(username)

        if username in clients:
            del clients[username]
        if username in games:
            del games[username]

        await broadcast_localized("User {} leave the dungeon...\n", username, exclude=username)
        writer.close()
        await writer.wait_closed()

        if game:
            print(game._("User {} disconnected").format(username))


async def send_messages(writer, username):
    """Send messages from queue to client.

    Args:
        writer: asyncio StreamWriter
        username (str): Recipient username
    """
    try:
        while True:
            message = await clients[username].get()
            writer.write(message.encode() + b'\n')
            await writer.drain()
    except asyncio.CancelledError:
        pass


async def wander_monsters():
    """Periodically move monsters around the game field."""
    global wandering_monsters_enabled
    while True:
        await asyncio.sleep(30)
        if not wandering_monsters_enabled:
            continue
        if not games:  # если нет подключенных клиентов
            continue
        game = next(iter(games.values()))

        if not monsters:
            print(game._("[SERVER] No monsters to move"))
            continue

        moved = False
        attempts = 0
        max_attempts = 100
            
        while not moved and attempts < max_attempts:
            attempts += 1
            name = random.choice(list(monsters))
            positions = []
            for x in range(10):
                for y in range(10):
                    if game_field[x][y] and game_field[x][y][0] == name:
                        positions.append((x, y))
            
            if not positions:
                continue
                
            x, y = random.choice(positions)
            direction = random.choice(['up', 'down', 'left', 'right'])
            
            new_x, new_y = x, y
            if direction == 'up':
                new_y = (y - 1) % 10
            elif direction == 'down':
                new_y = (y + 1) % 10
            elif direction == 'left':
                new_x = (x - 1) % 10
            elif direction == 'right':
                new_x = (x + 1) % 10
                
            if game_field[new_x][new_y] is None:
                monster = game_field[x][y]
                game_field[x][y] = None
                game_field[new_x][new_y] = monster
                moved = True
                
                print(f"[SERVER] Monster {name} moved from ({x},{y}) to ({new_x},{new_y})")
                
                # Локализованные направления
                dir_translation = {
                    'up': game._("up"),
                    'down': game._("down"),
                    'left': game._("left"),
                    'right': game._("right")
                }
                
                move_msg = game._("{name} moved one cell {direction}").format(
                    name=name,
                    direction=dir_translation[direction]
                )
                
                # Используем broadcast_localized вместо broadcast_message
                await broadcast_localized("[SERVER] {}", move_msg)

       
                for username, game in games.items():
                    if game.player_position == (new_x, new_y):
                        encounter_msg = game.encounter(new_x, new_y)
                        if encounter_msg:
                            await clients[username].put(encounter_msg)

def run_server(host='0.0.0.0', port=1337):
    """Run the MUD server with specified host and port."""
    async def inner_run():
        server = await asyncio.start_server(handle_client, host, port)
        addr = server.sockets[0].getsockname()
        print(f"[SERVER] Running on {addr[0]}:{addr[1]}")
        
        asyncio.create_task(wander_monsters())
        
        async with server:
            await server.serve_forever()
    
    asyncio.run(inner_run())

if __name__ == "__main__":
    run_server()
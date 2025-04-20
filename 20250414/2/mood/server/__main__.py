"""
Server module for MOOD MUD game.
"""

import random
import asyncio
import cowsay
import shlex
import gettext
import os
from pathlib import Path

LOCALE_DIR = Path(__file__).parent / 'locales'
translations = {
    'en_US': gettext.NullTranslations(),
    'ru_RU.UTF-8': gettext.translation('mood', LOCALE_DIR, ['ru'], fallback=True)
}

def _(text, locale='en_US'):
    """Translate text based on locale"""
    return translations.get(locale, translations['en_US']).gettext(text)

def ngettext(singular, plural, n, locale='en_US'):
    """Translate plural forms"""
    return translations.get(locale, translations['en_US']).ngettext(singular, plural, n)

clients = {}  
games = {}  

game_field = [[None for _ in range(10)] for _ in range(10)]
monsters = set()
wandering_monsters_enabled = True 

class MUD:
    """Main MUD game class handling player actions and game state.
    
    Attributes:
        player_position (tuple): Current player position (x, y)
        weapons (dict): Available weapons and their damage values
        username (str): Player's username
        jgsbat_func (function): Custom cow function for jgsbat monster
    """
    
    def __init__(self, username):
        """Initialize MUD instance for a player.
        
        Args:
            username (str): Player's username
        """
        self.player_position = (0, 0)
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
        self.username = username
        self.locale = 'en_US'  
        self.jgsbat_func = None
        try:
            with open("jgsbat.cow", "r", encoding="utf-8") as f:
                jgsbat_template = cowsay.read_dot_cow(f)
                self.jgsbat_func = lambda msg: cowsay.cowsay(msg, cowfile=jgsbat_template)
        except Exception as e:
            print(f"Failed to add jgsbat: {e}")

    def move_player(self, d_x, d_y):
        """Move player by delta coordinates.
        
        Args:
            d_x (int): X coordinate delta
            d_y (int): Y coordinate delta
            
        Returns:
            str: New position as "x y"
        """
        x, y = self.player_position
        x = (x + d_x) % 10
        y = (y + d_y) % 10
        self.player_position = (x, y)
        return f"{x} {y}"

    def encounter(self, x, y):
        """Handle monster encounter at specified coordinates.

        Args:
            x (int): X coordinate to check
            y (int): Y coordinate to check

        Returns:
            str: Formatted encounter message or empty string if no monster
        """
        monster = game_field[x][y]
        if monster:
            name, hello, _ = monster
            if name == "jgsbat" and self.jgsbat_func:
                return self.jgsbat_func(hello)
            return cowsay.cowsay(hello, cow=name)
        return ''

    def moving(self, d_x, d_y):
        """Move player and handle potential encounters.

        Args:
            d_x (int): X direction delta
            d_y (int): Y direction delta

        Returns:
            str: Move result with optional encounter message
        """
        new_position = self.move_player(d_x, d_y)
        encounter_message = self.encounter(self.player_position[0], self.player_position[1])
        if encounter_message:
            return f"Moved to ({new_position})\n{encounter_message}"
        return f"Moved to ({new_position})"

    def add_monster(self, x, y, hp, hello, name):
        """Add monster to game field.

        Args:
            x (int): X coordinate (0-9)
            y (int): Y coordinate (0-9)
            hp (int): Hit points (positive integer)
            hello (str): Greeting message
            name (str): Monster name

        Returns:
            str: "1" if replaced existing monster, "0" otherwise
                 or error message
        """
        if name not in cowsay.list_cows() and name != "jgsbat":
            return "cannot add unknown monster"
        if (x, y) == self.player_position:
            return "cannot add monster to player's position"

        old_mon = game_field[x][y] is not None
        game_field[x][y] = (name, hello, hp)
        monsters.add(name)
        return "1" if old_mon else "0"

    def attack(self, weapon, name):
        """Attack monster with specified weapon.

        Args:
            weapon (str): Weapon name (sword/spear/axe)
            name (str): Monster name

        Returns:
            str: Attack result formatted as "damage remaining_hp"
                 or error message
        """
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
async def send_localized(queue, locale, msg, *args):
    """Send localized message to client queue"""
    try:
        if any(isinstance(arg, int) for arg in args):
            # Handle plural forms
            last_num = next(arg for arg in reversed(args) if isinstance(arg, int))
            localized = ngettext(msg, msg.replace("hp", "hps"), last_num, locale) % args
        else:
            localized = _(msg, locale) % args
        await queue.put(localized)
    except Exception as e:
        print(f"Localization error: {e}")
        await queue.put(msg % args)  # Fallback to original

async def broadcast_localized(msg, *args, exclude=None):
    """Broadcast localized message to all clients"""
    for username, queue in clients.items():
        if username != exclude:
            await send_localized(queue, games[username].locale, msg, *args)

async def broadcast_message(message, exclude=None):
    """Send message to all connected clients.

    Args:
        message (str): Message to broadcast
        exclude (str, optional): Username to exclude from broadcast
    """
    for username, queue in clients.items():
        if username != exclude:
            await queue.put(message)
async def handle_client(reader, writer):
    """Handle incoming client connection with localization support"""
    username = (await reader.readline()).decode().strip()

    if username in clients:
        writer.write(_("Username already taken", 'en_US').encode() + b'\n')
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    clients[username] = asyncio.Queue()
    games[username] = MUD(username)

    # Send welcome message in client's locale
    welcome_msg = _("Welcome to MUD!", games[username].locale)
    writer.write(welcome_msg.encode() + b'\n')
    await writer.drain()

    await broadcast_localized("[SERVER] %s has joined the game", username, exclude=username)
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
                """Handle locale command: locale <lang>"""
                if len(parts) < 2:
                    await send_localized(clients[username], game.locale, 
                                       "Usage: locale <lang>")
                    continue
                
                lang = parts[1]
                if lang not in translations:
                    await send_localized(clients[username], game.locale,
                                       "Unsupported locale. Available: %s", 
                                       ", ".join(translations.keys()))
                    continue
                
                game.locale = lang
                await send_localized(clients[username], lang, 
                                    "Set up locale: %s", lang)

            elif cmd == "addmon":
                """Handle addmon command with localization"""
                try:
                    name, x, y, hp = parts[1:5]
                    hello = ' '.join(parts[5:])
                    x, y, hp = map(int, [x, y, hp])
                    
                    if name not in cowsay.list_cows() and name != "jgsbat":
                        await send_localized(clients[username], game.locale,
                                           "cannot add unknown monster")
                        continue
                    
                    if (x, y) == game.player_position:
                        await send_localized(clients[username], game.locale,
                                           "cannot add monster to player's position")
                        continue
                    
                    if x < 0 or x >= 10 or y < 0 or y >= 10 or hp <= 0:
                        await send_localized(clients[username], game.locale,
                                           "Invalid arguments")
                        continue

                    old_mon = game_field[x][y] is not None
                    game_field[x][y] = (name, hello, hp)
                    monsters.add(name)
                    
                    if old_mon:
                        await broadcast_localized(
                            "[SERVER] %s added monster %s to (%d, %d) with %d hp\n" +
                            _("Replaced the old monster", game.locale),
                            username, name, x, y, hp,
                            exclude=username
                        )
                    else:
                        await broadcast_localized(
                            "[SERVER] %s added monster %s to (%d, %d) with %d hp",
                            username, name, x, y, hp,
                            exclude=username
                        )
                except (ValueError, IndexError):
                    await send_localized(clients[username], game.locale,
                                       "Invalid arguments")

            elif cmd == "attack":
                """Handle attack command with localized HP messages"""
                try:
                    weapon, name = parts[1:3]
                    if weapon not in game.weapons:
                        await send_localized(clients[username], game.locale,
                                           "Unknown weapon")
                        continue
                    
                    if name not in monsters:
                        await send_localized(clients[username], game.locale,
                                           "no such monster %s", name)
                        continue

                    x, y = game.player_position
                    monster = game_field[x][y]
                    if not monster or monster[0] != name:
                        await send_localized(clients[username], game.locale,
                                           "no %s here", name)
                        continue

                    _, _, hp = monster
                    damage = min(game.weapons[weapon], hp)
                    hp -= damage
                    
                    if hp <= 0:
                        game_field[x][y] = None
                        monsters.remove(name)
                        await broadcast_localized(
                            "[SERVER] %s attacked %s with %s for %d hp, %s died",
                            username, name, weapon, damage, name
                        )
                    else:
                        game_field[x][y] = (name, _, hp)
                        await broadcast_localized(
                            "[SERVER] %s attacked %s with %s for %d hp, %s has %d hp left",
                            username, name, weapon, damage, name, hp
                        )
                except (ValueError, IndexError):
                    await send_localized(clients[username], game.locale,
                                       "Invalid arguments")

            elif cmd == "move":
                """Handle move command: move dx dy"""
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
                """Handle sayall command: sayall message"""
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

            elif cmd == "movemonsters":
                """Handle movemonsters command: movemonsters on/off"""
                try:
                    global wandering_monsters_enabled
                    state = parts[1].lower()
                    if state == "on":
                        if not wandering_monsters_enabled:
                            wandering_monsters_enabled = True
                            await broadcast_message(f"Moving monsters: on")
                        else:
                            await clients[username].put("Moving monsters: on")
                    elif state == "off":
                        if wandering_monsters_enabled:
                            wandering_monsters_enabled = False
                            await broadcast_message(f"Moving monsters: off")
                        else:
                            await clients[username].put("Moving monsters: off")
                    else:
                        await clients[username].put("Invalid argument. Use 'on' or 'off'")
                except IndexError:
                    await clients[username].put("Invalid arguments. Usage: movemonsters on|off")

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

        await broadcast_localized("[SERVER] %s has left the game", username, exclude=username)
        writer.close()
        await writer.wait_closed()
        print(f"{username} disconnected")


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
        if not monsters:
            print("[SERVER] No monsters to move")
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
                
                # Логирование на сервере
                print(f"[SERVER] Monster {name} moved from ({x},{y}) to ({new_x},{new_y})")
                
                # Уведомление всех клиентов
                move_msg = f"{name} moved one cell {direction}"
                await broadcast_message(f"[SERVER] {move_msg}")
                print(f"[SERVER] {move_msg}")

                # Проверка встречи с игроками
                for username, game in games.items():
                    if game.player_position == (new_x, new_y):
                        encounter_msg = game.encounter(new_x, new_y)
                        if encounter_msg:
                            await clients[username].put(encounter_msg)

async def main():
    """Main server entry point."""
    server = await asyncio.start_server(handle_client, '0.0.0.0', 1337)
    addr = server.sockets[0].getsockname()
    print(f"[SERVER] Запущен на {addr[0]}:{addr[1]}")
    
    asyncio.create_task(wander_monsters())
    
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

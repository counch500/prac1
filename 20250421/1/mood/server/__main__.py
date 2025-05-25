"""MUD (Multi-User Dungeon) game server module.

This module implements a multiplayer text-based adventure game server.
Players can move around a 10x10 grid, encounter monsters, fight them,
and communicate with other players.

The server uses asyncio for handling multiple client connections
and implements game mechanics including monster movement, combat,
and player interactions.
"""

import asyncio
import cowsay
import shlex
import random
import locale
import gettext
import os

clients = {}
games = {}
client_locales = {}

game_field = [[None for _ in range(10)] for _ in range(10)]
monsters = {}
wandering_monsters_enabled = True

LOCALES = {
    ("ru_RU", "UTF-8"): gettext.translation("mud", "mood/locale", ["ru_RU.UTF-8"]),
    ("en_US", "UTF-8"): gettext.NullTranslations()
}

def _(text, client_locale=None):
    """Translate a message to the specified locale.
    
    Args:
        text (str): Message to translate
        client_locale (tuple, optional): Target locale tuple (language, encoding). If None, returns original message.
        
    Returns:
        str: Translated message or original if translation not available
    """
    if not client_locale or client_locale not in LOCALES:
        return text
    return LOCALES[client_locale].gettext(text)

def ngettext(singular, plural, n, client_locale=None):
    """Translate a message with plural forms.
    
    Args:
        singular (str): Singular form of the message
        plural (str): Plural form of the message
        n (int): Number to determine which form to use
        client_locale (tuple, optional): Target locale tuple (language, encoding). If None, returns original message.
        
    Returns:
        str: Translated message or original if translation not available
    """
    if not client_locale or client_locale not in LOCALES:
        return singular if n == 1 else plural
    return LOCALES[client_locale].ngettext(singular, plural, n)

class MUD:
    """Main game class representing a player's game session.

    This class manages player state, including position, weapons,
    and interactions with monsters. It also handles special
    monster types like jgsbat.

    Attributes:
        player_position (tuple): Current (x, y) position of the player.
        weapons (dict): Available weapons and their damage values.
        username (str): Player's username.
        jgsbat_func (function): Special function for jgsbat monster display.
    """

    def __init__(self, username):
        """Initialize a new MUD game instance.

        Args:
            username (str): Player's username.
        """
        self.username = username
        self.player_position = (0, 0)
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
        self.jgsbat_func = None
        try:
            with open("jgsbat.cow", "r", encoding="utf-8") as f:
                jgsbat_template = cowsay.read_dot_cow(f)
                self.jgsbat_func = lambda msg: cowsay.cowsay(msg, cowfile=jgsbat_template)
        except Exception as e:
            print(f"Ошибка загрузки монстра jgsbat: {e}")

    def move_player(self, d_x, d_y):
        """Move the player to a new position.

        Args:
            d_x (int): Change in x-coordinate.
            d_y (int): Change in y-coordinate.

        Returns:
            tuple: New player position (x, y).
        """
        self.player_position = ((self.player_position[0] + d_x) % 10, (self.player_position[1] + d_y) % 10)
        return self.player_position

    def encounter(self, x, y):
        """Handle player encounter with a monster.

        Args:
            x (int): X-coordinate of encounter.
            y (int): Y-coordinate of encounter.

        Returns:
            str: Monster's greeting message or empty string if no monster.
        """
        monster = game_field[x][y]
        if monster:
            name, hello, _ = monster
            if name == "jgsbat" and self.jgsbat_func:
                return self.jgsbat_func(hello)
            return cowsay.cowsay(hello, cow=name)
        return ''

    def moving(self, d_x, d_y):
        """Process player movement and check for encounters.

        Args:
            d_x (int): Change in x-coordinate.
            d_y (int): Change in y-coordinate.

        Returns:
            str: Movement result and any encounter messages.
        """
        new_position = self.move_player(d_x, d_y)
        encounter_message = self.encounter(new_position[0], new_position[1])
        if encounter_message:
            return f"Moved to ({new_position[0]}, {new_position[1]})\n{encounter_message}"
        return f"Moved to ({new_position[0]}, {new_position[1]})"

    def add_monster(self, x, y, hp, hello, name):
        """Add a new monster to the game field.

        Args:
            x (int): X-coordinate for monster placement.
            y (int): Y-coordinate for monster placement.
            hp (int): Monster's hit points.
            hello (str): Monster's greeting message.
            name (str): Monster's name.

        Returns:
            str: Status message indicating success or failure.
        """
        if name not in cowsay.list_cows() and name != "jgsbat":
            return "cannot add unknown monster"
        if (x, y) == self.player_position:
            return "cannot add monster to player's position"

        old_mon = game_field[x][y] is not None
        game_field[x][y] = (name, hello, hp)
        monsters[(x, y)] = name
        return "1" if old_mon else "0"

    def attack(self, weapon, name):
        """Attack a monster with a weapon.

        Args:
            weapon (str): Name of the weapon to use.
            name (str): Name of the monster to attack.

        Returns:
            str: Attack result including damage dealt and remaining HP.
        """
        x, y = self.player_position
        monster = game_field[x][y]
        if not monster or monster[0] != name:
            return f'no {name} here'
        name, hello, hp = monster
        damage = min(self.weapons[weapon], hp)
        hp -= damage
        if hp <= 0:
            game_field[x][y] = None
            del monsters[(x, y)]
            return f'{damage} 0'
        game_field[x][y] = (name, hello, hp)
        return f'{damage} {hp}'

def answer(fun=None, client_locale=None, **kwargs):
    """Format and translate messages based on function type.
    
    Args:
        fun (str, optional): Function type (addmon, attack, etc.)
        client_locale (tuple, optional): Target locale tuple (language, encoding)
        **kwargs: Arguments for message formatting
        
    Returns:
        str: Formatted and translated message
    """
    match fun:
        case 'addmon':
            replaced = '' if kwargs.get('state', 0) == 0 else _("Replaced the old monster", client_locale)
            return _("{username} added monster {name} to ({x}, {y}) with {hp} {hp_text}\n", client_locale) + replaced
        case 'attack':
            if kwargs.get('state', 0) == 0:
                return _("{username} attacked {name} with {weapon} for {damage} {hp_text}, {name} died", client_locale)
            else:
                return _("{username} attacked {name} with {weapon} for {damage} {damage_hp}, {name} has {hp} {hp_text} left", client_locale)
        case 'join':
            return _("{username} has joined the game", client_locale)
        case 'leave':
            return _("{username} has left the game", client_locale)
        case 'movemonsters':
            return _("Moving monsters: {status}", client_locale)

        case 'monster_move':
            return _("{name} moved one cell {direction}", client_locale)
        case 'sayall':
            return _("{username}: {message}", client_locale)
        case _:
            return kwargs.get('message', '')

async def broadcast_message(fun=None, exclude=None, **kwargs):
    """Send a message to all connected clients.

    Args:
        message (str): Message to broadcast (can be a format string).
        exclude (str, optional): Username to exclude from broadcast.
        **kwargs: Format arguments for the message.
    """
    for username, queue in clients.items():
        if username != exclude:
            client_kwargs = kwargs.copy()
            
            if 'hp_text' in client_kwargs:
                n = client_kwargs.get('hp', 0)
                client_kwargs['hp_text'] = ngettext("hp", "hp", n, client_locales[username])
            if 'damage_hp' in client_kwargs:
                n = client_kwargs.get('damage', 0)
                client_kwargs['damage_hp'] = ngettext("hp", "hp", n, client_locales[username])
            
            translated_message = answer(fun, client_locales[username], **kwargs)
            formatted_message = translated_message.format(**client_kwargs)
            await queue.put(formatted_message)

async def move_random_monster():
    """Periodically move random monsters around the game field.

    This function runs every 30 seconds and:
    1. Selects a random monster
    2. Attempts to move it in a random direction
    3. Broadcasts movement messages
    4. Handles player encounters
    """
    while True:
        await asyncio.sleep(30)
        
        if not wandering_monsters_enabled:
            continue
        
        # Собираем всех монстров и их позиции
        monster_positions = []
        for x in range(10):
            for y in range(10):
                if game_field[x][y] is not None:
                    name, hello, hp = game_field[x][y]
                    monster_positions.append((x, y, name))
        
        if not monster_positions:
            print("[Server] No monsters to move")
            continue
        
        moved = False
        attempts = 0
        max_attempts = 100  # Лимит попыток для предотвращения бесконечного цикла
        
        while not moved and attempts < max_attempts:
            attempts += 1
            # Выбираем случайного монстра
            x, y, name = random.choice(monster_positions)
            
            # Выбираем направление
            direction = random.choice(['right', 'left', 'up', 'down'])
            new_x, new_y = x, y
            
            # Вычисляем новую позицию
            if direction == 'right':
                new_x = (x + 1) % 10
            elif direction == 'left':
                new_x = (x - 1) % 10
            elif direction == 'up':
                new_y = (y - 1) % 10
            elif direction == 'down':
                new_y = (y + 1) % 10
            
            # Проверяем, свободна ли клетка
            if game_field[new_x][new_y] is None:
                # Перемещаем монстра
                monster = game_field[x][y]
                game_field[x][y] = None
                game_field[new_x][new_y] = monster
                
                # Обновляем позицию в словаре монстров
                del monsters[(x, y)]
                monsters[(new_x, new_y)] = name
                
                # Отправляем сообщение игрокам
                move_msg = f"{name} moved one cell {direction}"
                await broadcast_message(message=move_msg)
                
                # Проверяем столкновение с игроками
                for username, game in games.items():
                    px, py = game.player_position
                    if (px, py) == (new_x, new_y):
                        encounter_message = game.encounter(new_x, new_y)
                        if encounter_message:
                            await clients[username].put(f"Moved to ({new_x}, {new_y})\n{encounter_message}")
                
                moved = True
                print(f"[Server] {move_msg}")

        if not moved:
            print("[Server] Failed to move any monster after 100 attempts")

async def handle_client(reader, writer):
    """Handle individual client connections.

    This function manages the lifecycle of a client connection,
    including authentication, command processing, and cleanup.

    Args:
        reader (StreamReader): Client's input stream.
        writer (StreamWriter): Client's output stream.
    """
    username = (await reader.readline()).decode().strip()

    if username in clients:
        writer.write(b"Username already taken\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    clients[username] = asyncio.Queue()
    games[username] = MUD(username)
    client_locales[username] = ("en_US", "UTF-8")

    writer.write(b"Welcome to MUD!\n")
    await writer.drain()

    await broadcast_message('join', exclude=username, username=username)
    print(f"{username} connected")

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
                if len(parts) != 2:
                    await clients[username].put("Invalid arguments")
                    continue
                
                locale_str = parts[1]
                if locale_str == "ru_RU.UTF-8":
                    client_locales[username] = ("ru_RU", "UTF-8")
                elif locale_str == "en_US.UTF-8":
                    client_locales[username] = ("en_US", "UTF-8")
                else:
                    await clients[username].put(f"Unsupported locale: {locale_str}")
                    continue
                    
                translated = _("Set up locale: {locale}", client_locales[username])
                await clients[username].put(translated.format(locale=locale_str))

            elif cmd == "movemonsters":
                if len(parts) != 2 or parts[1] not in ["on", "off"]:
                    await clients[username].put("Invalid arguments")
                    continue
                
                global wandering_monsters_enabled
                wandering_monsters_enabled = (parts[1] == "on")
                status = "on" if wandering_monsters_enabled else "off"
                await broadcast_message(
                    fun='movemonsters',
                    status=status,
                    exclude=username
                )
                confirmation = answer(
                    'movemonsters', 
                    client_locales[username], 
                    status=status
                ).format(status=status)
                await clients[username].put(confirmation)

            elif cmd == "addmon":
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
                    monsters[(x, y)] = name
                    
                    await broadcast_message('addmon',
                        username=username,
                        name=name,
                        x=x,
                        y=y,
                        hp=hp,
                        hp_text=ngettext("hp", "hp", hp, client_locales[username]),
                        state=1 if old_mon else 0
                    )
                except (ValueError, IndexError):
                    await clients[username].put("Invalid arguments")

            elif cmd == "attack":
                try:
                    weapon, name = parts[1:3]
                    if weapon not in ["sword", "spear", "axe"]:
                        await clients[username].put("Unknown weapon")
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
                        del monsters[(x, y)]
                        await broadcast_message('attack',
                            username=username,
                            name=name,
                            weapon=weapon,
                            damage=damage,
                            hp_text=ngettext("hp", "hp", damage, client_locales[username]),
                            state=0
                        )
                    else:
                        game_field[x][y] = (name, hello, hp)
                        await broadcast_message('attack',
                            username=username,
                            name=name,
                            weapon=weapon,
                            damage=damage,
                            damage_hp=ngettext("hp", "hp", damage, client_locales[username]),
                            hp=hp,
                            hp_text=ngettext("hp", "hp", hp, client_locales[username]),
                            state=1
                        )
                except (ValueError, IndexError):
                    await clients[username].put("Invalid arguments")

            elif cmd == "move":
                try:
                    d_x, d_y = map(int, parts[1:3])
                    new_position = game.move_player(d_x, d_y)
                    encounter_message = game.encounter(new_position[0], new_position[1])
                    if encounter_message:
                        await clients[username].put(f"Moved to ({new_position[0]}, {new_position[1]})\n{encounter_message}")
                    else:
                        await clients[username].put(f"Moved to ({new_position[0]}, {new_position[1]})")
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
                    translated = _("{username}: {message}", client_locales[username])
                    await broadcast_message(
                        fun='sayall', 
                        message=msg_to_broadcast, 
                        exclude=username, 
                        username=username
                    )
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
        if username in client_locales:
            del client_locales[username]

        await broadcast_message('leave', exclude=username, username=username)

        writer.close()
        await writer.wait_closed()
        print(f"{username} disconnected")

async def send_messages(writer, username):
    """Send queued messages to a specific client.

    Args:
        writer (StreamWriter): Client's output stream.
        username (str): Client's username.
    """
    try:
        while True:
            message = await clients[username].get()
            writer.write(message.encode() + b'\n')
            await writer.drain()
    except asyncio.CancelledError:
        pass

async def main():
    """Start the MUD game server.

    This function initializes the server and starts the monster
    movement task before beginning to accept client connections.
    """
    server = await asyncio.start_server(handle_client, '0.0.0.0', 1337)
    addr = server.sockets[0].getsockname()
    print(f"MUD Server started. Listening on {addr[0]}:{addr[1]}")
    print("Type Ctrl+C to stop the server\n")
    
    asyncio.create_task(move_random_monster())
    
    async with server:
        await server.serve_forever()

def serve():
    asyncio.run(main())

if __name__ == "__main__":
    serve()

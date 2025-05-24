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
import gettext
import os

# Initialize translations
translations = {
    'ru_RU.UTF8': gettext.translation('mud', localedir='locale', languages=['ru_RU']),
    'en_US.UTF8': gettext.NullTranslations()
}

# Default locale
DEFAULT_LOCALE = 'en_US.UTF8'

clients = {}  # Словарь для хранения подключенных пользователей
games = {}    # Словарь для хранения игровых сессий

# Глобальные переменные для хранения общего состояния игры
game_field = [[None for _ in range(10)] for _ in range(10)]
monsters = set()
wandering_monsters_enabled = True  # Флаг включения/выключения бродячих монстров

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
        locale (str): Player's preferred locale.
    """

    def __init__(self, username):
        """Initialize a new player session.

        Args:
            username (str): The player's chosen username.
        """
        self.player_position = (0, 0)
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
        self.username = username
        self.jgsbat_func = None
        self.locale = DEFAULT_LOCALE
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
            str: New position coordinates as a string.
        """
        x, y = self.player_position
        x = (x + d_x) % 10
        y = (y + d_y) % 10
        self.player_position = (x, y)
        return f"{x} {y}"

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
        encounter_message = self.encounter(self.player_position[0], self.player_position[1])
        if encounter_message:
            return f"Moved to ({new_position})\n{encounter_message}"
        return f"Moved to ({new_position})"

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
        monsters.add(name)
        return "1" if old_mon else "0"

    def attack(self, weapon, name):
        """Attack a monster with a weapon.

        Args:
            weapon (str): Name of the weapon to use.
            name (str): Name of the monster to attack.

        Returns:
            str: Attack result including damage dealt and remaining HP.
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

async def broadcast_message(message, exclude=None, **kwargs):
    """Send a message to all connected clients."""
    for username, queue in clients.items():
        if username != exclude:
            game = games[username]
            _ = translations[game.locale].gettext
            ngettext = translations[game.locale].ngettext
            # Форматируем сообщение с учетом локали получателя
            formatted_message = format_message(message, game.locale, **kwargs)
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
        await asyncio.sleep(30)  # Ждем 30 секунд
        
        if not wandering_monsters_enabled:
            continue  # Пропускаем итерацию, если режим выключен
        
        # Получаем список всех монстров и их позиций
        monster_positions = []
        for x in range(10):
            for y in range(10):
                if game_field[x][y] is not None:
                    monster_positions.append((x, y, game_field[x][y]))
        
        if not monster_positions:
            continue  # Если нет монстров, пропускаем итерацию
        
        # Выбираем случайного монстра
        x, y, monster = random.choice(monster_positions)
        name, hello, hp = monster
        
        # Пробуем переместить монстра, пока не найдем свободную клетку
        moved = False
        while not moved:
            # Выбираем случайное направление
            direction = random.choice(['right', 'left', 'up', 'down'])
            new_x, new_y = x, y
            
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
                game_field[new_x][new_y] = monster
                game_field[x][y] = None
                
                # Отправляем сообщение о перемещении всем игрокам
                await broadcast_message(f"{name} moved one cell {direction}")
                
                # Проверяем, не попал ли монстр на клетку с игроком
                for username, game in games.items():
                    if game.player_position == (new_x, new_y):
                        encounter_message = game.encounter(new_x, new_y)
                        if encounter_message:
                            await clients[username].put(encounter_message)
                
                moved = True

def get_plural_form(n, locale):
    """Get the correct plural form for a number based on locale."""
    if locale == 'ru_RU.UTF8':
        if n % 10 == 1 and n % 100 != 11:
            return 0  # singular
        elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            return 1  # few
        else:
            return 2  # many
    return 0  # English only has singular/plural

def format_message(message, locale, **kwargs):
    """Format a message with proper plural forms for the given locale."""
    _ = translations[locale].gettext
    ngettext = translations[locale].ngettext
    
    if 'hp' in kwargs:
        hp = kwargs['hp']
        if locale == 'ru_RU.UTF8':
            kwargs['hp'] = ngettext("{n} очко здоровья", "{n} очков здоровья", hp).format(n=hp)
        else:
            kwargs['hp'] = f"{hp} hp"
    
    if 'damage' in kwargs:
        damage = kwargs['damage']
        if locale == 'ru_RU.UTF8':
            kwargs['damage'] = ngettext("{n} урон", "{n} урона", damage).format(n=damage)
        else:
            kwargs['damage'] = f"{damage} damage"
    
    return _(message).format(**kwargs)

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

    writer.write(b"Welcome to MUD!\n")
    await writer.drain()

    # Отправляем сообщение о присоединении всем, кроме самого пользователя
    await broadcast_message("{username} has joined the game", exclude=username, username=username)
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
            
            # Get translation functions for current locale
            _ = translations[game.locale].gettext
            ngettext = translations[game.locale].ngettext

            if cmd == "locale":
                if len(parts) != 2:
                    await clients[username].put(format_message(_("Invalid arguments"), game.locale))
                    continue
                
                new_locale = parts[1]
                if new_locale in translations:
                    game.locale = new_locale
                    await clients[username].put(format_message(_("Set up locale: {args}"), game.locale, args=new_locale))
                else:
                    await clients[username].put(format_message(_("Unsupported locale"), game.locale))

            elif cmd == "movemonsters":
                if len(parts) != 2 or parts[1] not in ["on", "off"]:
                    await clients[username].put(format_message(_("Invalid arguments"), game.locale))
                    continue
                
                global wandering_monsters_enabled
                wandering_monsters_enabled = (parts[1] == "on")
                await broadcast_message("Moving monsters: {args}", args=parts[1])

            elif cmd == "addmon":
                try:
                    name, x, y, hp = parts[1:5]
                    hello = ' '.join(parts[5:])
                    x, y, hp = map(int, [x, y, hp])
                    
                    if name not in cowsay.list_cows() and name != "jgsbat":
                        await clients[username].put(format_message(_("Cannot add unknown monster"), game.locale))
                        continue
                    if (x, y) == game.player_position:
                        await clients[username].put(format_message(_("Cannot add monster to player's position"), game.locale))
                        continue
                    if x < 0 or x >= 10 or y < 0 or y >= 10 or hp <= 0:
                        await clients[username].put(format_message(_("Invalid arguments"), game.locale))
                        continue

                    old_mon = game_field[x][y] is not None
                    game_field[x][y] = (name, hello, hp)
                    monsters.add(name)
                    
                    await broadcast_message("{username} added monster {name} to ({x}, {y}) with {hp}", 
                                          username=username, name=name, x=x, y=y, hp=hp)
                    if old_mon:
                        await broadcast_message("Replaced the old monster")
                except (ValueError, IndexError):
                    await clients[username].put(format_message(_("Invalid arguments"), game.locale))

            elif cmd == "attack":
                try:
                    weapon, name = parts[1:3]
                    if weapon not in ["sword", "spear", "axe"]:
                        await clients[username].put(format_message(_("Unknown weapon"), game.locale))
                        continue
                    if name not in monsters:
                        await clients[username].put(format_message(_("No such monster {name}"), game.locale, name=name))
                        continue

                    x, y = game.player_position
                    monster = game_field[x][y]
                    if not monster or monster[0] != name:
                        await clients[username].put(format_message(_("No {name} here"), game.locale, name=name))
                        continue

                    name, hello, hp = monster
                    damage = min(game.weapons[weapon], hp)
                    hp -= damage
                    
                    if hp <= 0:
                        game_field[x][y] = None
                        monsters.remove(name)
                        await broadcast_message("{username} attacked {name} with {weapon} for {damage}, {name} died", 
                                              username=username, name=name, weapon=weapon, damage=damage)
                    else:
                        game_field[x][y] = (name, hello, hp)
                        await broadcast_message("{username} attacked {name} with {weapon} for {damage}, {name} has {hp} left", 
                                              username=username, name=name, weapon=weapon, damage=damage, hp=hp)
                except (ValueError, IndexError):
                    await clients[username].put(format_message(_("Invalid arguments"), game.locale))

            elif cmd == "move":
                try:
                    d_x, d_y = map(int, parts[1:3])
                    new_position = game.move_player(d_x, d_y)
                    encounter_message = game.encounter(game.player_position[0], game.player_position[1])
                    if encounter_message:
                        await clients[username].put(format_message(_("Moved to ({new_position})\n{encounter_message}"), game.locale,
                                                                 new_position=new_position, encounter_message=encounter_message))
                    else:
                        await clients[username].put(format_message(_("Moved to ({new_position})"), game.locale,
                                                                 new_position=new_position))
                except (ValueError, IndexError):
                    await clients[username].put(format_message(_("Invalid arguments"), game.locale))

            elif cmd == "sayall":
                if not parts[1:]:
                    await clients[username].put(format_message(_("Invalid arguments"), game.locale))
                    continue
                message = ' '.join(parts[1:])
                await broadcast_message("{username}: {message}", username=username, message=message)

            else:
                await clients[username].put(format_message(_("Unknown command"), game.locale))

        await broadcast_message("{username} has left the game", username=username, exclude=username)

        writer.close()
        await writer.wait_closed()
        print(f"{username} disconnected")

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
    
    # Запускаем задачу перемещения монстров
    asyncio.create_task(move_random_monster())
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
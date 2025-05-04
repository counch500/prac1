"""Run server"""
import asyncio
import cowsay
from io import StringIO
import shlex
import random
import gettext
import locale

COWS = cowsay.list_cows() + ['jgsbat']

JGSBAT = cowsay.read_dot_cow(StringIO(r"""
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\\--//|.'-._  (
     )'   .'\/o\/o\/'.   `(
      ) .' . \====/ . '. (
       )  / <<    >> \  (
        '-._/``  ``\_.-'
  jgs    __\\\'--'//__
         (((""`  `"")))
"""))

LOCALES = {
    ("ru_RU", "UTF-8"): gettext.translation("mud", "po", ["ru"]),
    ("en_US", "UTF-8"): gettext.NullTranslations()
}
locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

def _(text):
    return LOCALES[locale.getlocale()].gettext(text)


class Error(BaseException):
    """Class of errors that are detected by server"""
    def __init__(self, code, name=''):
        """
        Define error

        code:int identifier of the Error
        name:str name of the cow that is used in one error message
        """
        match code:
            case 1:
                self.text = _("Invalid arguments")
            case 2:
                self.text = _("Cannot add unknown monster")
            case 3:
                self.text = _("No {name} here").format(name=name)
            case 4:
                self.text = _("Unknown weapon")


class Player:
    """Class with basic users characteristics and actions"""
    def __init__(self):
        """Player is set on (0, 0) position"""
        self.x, self.y = 0, 0
        self.queue = asyncio.Queue()
        self.lang = locale.getlocale()

    def move(self, d_x, d_y):
        """
        Funtion to move player

        d_x: -1 or 0 or 1
        d_y: -1 or 0 or 1
        """
        self.x = (self.x + d_x) % 10
        self.y = (self.y + d_y) % 10
        return _("Moved to ({x}, {y})\n").format(x=self.x, y=self.y)

    def set_locale(self, args):
        if args == 'ru_RU.UTF8\n':
            self.lang = ('ru_RU', 'UTF-8')
        elif args == 'en_US.UTF8\n':
            self.lang = ('en_US', 'UTF-8')
        else:
            raise Error(1)
        locale.setlocale(locale.LC_ALL, self.lang)
        return _("Set up locale: {args}").format(args=args)


class Monster:
    """Class with basic monsters characteristics and actions"""
    def __init__(self, x, y, name, phrase, hitpoints):
        """
        Set monster

        x:int first coordinate
        y:int seconf coordinate
        name:str name of the monster
        phrase:str string to be print when user encounts monster
        hitpoints:int number of hitpoints
        """
        self.x = x
        self.y = y
        self.phrase = phrase
        self.cow = name
        self.hp = hitpoints

    def say(self):
        """Return cow with phrase"""
        global JGSBAT
        if self.cow == 'jgsbat':
            return cowsay.cowsay(self.phrase, cowfile=JGSBAT)
        else:
            return cowsay.cowsay(self.phrase, cow=self.cow)


class Game:
    """Class to process game"""
    def __init__(self):
        """Initialize characteristics"""
        self.size = 10
        self.monsters = {}
        self.mode = True

    def encounter(self, x, y):
        """
        Return monster when user meets it

        x:int first coordinate of the player
        y:int second coordinate of the player
        """
        if self.monsters[(x, y)]:
            return self.monsters[(x, y)].say()
        return ''

    def moving(self, player, d_x, d_y):
        """
        Move

        player:Player current player
        d_x: -1 or 0 or 1
        d_x: -1 or 0 or 1
        """
        s = player.move(d_x, d_y)
        if (player.x, player.y) in self.monsters:
            s += self.encounter(player.x, player.y)
        return s

    def add_monster(self, x, y, hp, hello, name):
        """
        Add monster

        x:int first coordinate
        y:int second coordinate
        hp:int number of hitpoints
        hello:str phrase to be said by monster
        name:str name of the monster
        """
        ans = {'name': name, 
               'x': x, 'y': y,
               'hello': hello}
        if (x, y) in self.monsters and not (self.monsters[(x, y)] is None):
            ans['state'] = 1
        else:
            ans['state'] = 0
        self.monsters[(x, y)] = Monster(x, y, name, hello, hp)
        return ans

    def attack(self, x, y, weapon, name):
        """
        Attack

        x:int first coordinate
        y:int second coordinate
        weapon: sword, spear or axe
        name: name of the monster to be attacked
        """
        if ((x, y) not in self.monsters or self.monsters[(x, y)] is None or self.monsters[(x, y)].cow != name):
            raise Error(3, name)
        damage = min(self.monsters[(x, y)].hp, weapon)
        self.monsters[(x, y)].hp = self.monsters[(x, y)].hp - damage
        ans = {'name': self.monsters[(x, y)].cow,
               'damage': damage}
        if self.monsters[(x, y)].hp == 0:
            ans['state'] = 0
            self.monsters[(x, y)] = None
        else:
            ans['state'] = 1
            ans['hp'] = self.monsters[(x, y)].hp
        return ans

    def set_mode(self, args):
        """
        Turn on/off wanfering monsters

        args:str on or off
        """
        if args not in ['on\n', 'off\n']:
            raise Error(1)
        if args == 'on\n':
            self.mode = True
        else:
            self.mode = False
        return _('Moving monsters: {args}').format(args=args)


def parse_args(args, param):
    """
    Parse args

    params:dict parameters to be parsed
    """
    args_parsed = {}
    for i in param:
        if i not in args:
            return None
        args_parsed[i] = args[args.index(i) + 1: args.index(i) + 1 + param[i]]
    return args_parsed


def add_monster_check(args):
    """
    Check addmon

    args:str args to be checked
    """
    preprocess = shlex.split(args)
    if len(preprocess) != 8:
        raise Error(1)
    name = preprocess[0]
    parsed_args = parse_args(preprocess[1:], {"hello": 1, "hp": 1, "coords": 2})
    if not parsed_args:
        raise Error(1)
    x, y = parsed_args['coords']
    hello = parsed_args['hello'][0]
    hp = parsed_args['hp'][0]
    if (not x.isdigit() or not y.isdigit() or not hp.isdigit()):
        raise Error(1)
    x, y, hp = map(int, [x, y, hp])
    if x < 0 or x >= 10 or y < 0 or y >= 10 or hp <= 0:
        raise Error(1)
    if name not in COWS:
        raise Error(2)
    return x, y, hp, hello, name


def attack_check(args):
    """
    Check attack

    args:str args to be checked
    """
    splitted = shlex.split(args)
    parsed_args = parse_args(splitted, {'with': 1})
    if parsed_args:
        match parsed_args['with'][0]:
            case 'sword': weapon = 10
            case 'spear': weapon = 15
            case 'axe': weapon = 20
            case _:
                raise Error(4)
    else:
        weapon = 10
    if len(args) == 0 or splitted[0] not in COWS:
        raise Error(1)
    name = splitted[0]
    return weapon, name

def answer(fun=None, name='', x=0, y=0, hello='', login='', damage=0, state=0, hp=0):
    match fun:
        case 'addmon':
            replaced = '' if state == 0 else _("Replaced the old monster\n") 
            return _("Added monster {name} to ({x}, {y}) saying {hello}\n{replaced}").format(name=name,
                                                                                             x=x, y=y,
                                                                                             hello=hello,
                                                                                             replaced=replaced)
        case 'attack':
            if state == 0:
                health =_("{name} died\n").format(name=name)
            else:
                health = (_("{name} now has").format(name=name) 
                          + LOCALES[locale.getlocale()].ngettext(" {hp} hit point\n", " {hp} hit points\n", hp).format(hp=hp))
            return (_("{login} attacked {name}").format(login=login, name=name)
                   + LOCALES[locale.getlocale()].ngettext(", damage {damage} hit point\n", ", damage {damage} hit points\n", damage).format(damage=damage)
                   + health)
        case 'new':
            return _('New player: {login}').format(login=login)
        case 'left':
            return _("{login} left").format(login=login)

async def send_all(mes='', fun=None, args={}, exception=None):
    """
    Send message to all users

    mes:str message to be sent
    exception:Player player that dont receive this message
    """
    default_loc = locale.getlocale()
    for out in players.values():
        locale.setlocale(locale.LC_ALL, out.lang)
        if out != exception:
            if fun:
                mes = answer(fun=fun, **args)
            await out.queue.put(f"{mes}")
    locale.setlocale(locale.LC_ALL, default_loc)

async def echo(reader, writer):
    """Run game"""
    global game, players

    send = asyncio.create_task(reader.readline())

    await asyncio.wait_for(send, timeout=None)
    login = send.result().decode()[:-1]
    if login in players:
        writer.write('0'.encode())
        writer.close()
        send.cancel()
        await writer.wait_closed()
        return
    else:
        players[login] = Player()
        receive = asyncio.create_task(players[login].queue.get())
        writer.write("1".encode())
        await send_all(fun='new', args={'login':login}, exception=players[login])

    me = "{}:{}".format(*writer.get_extra_info('peername'))

    while not reader.at_eof():
        done, pending = await asyncio.wait([send, receive], return_when=asyncio.FIRST_COMPLETED)
        for request in done:
            if request is send:
                send = asyncio.create_task(reader.readline())
                match request.result().decode().split(maxsplit=1):
                    case ['addmon', args]:
                        try:
                            x, y, hp, hello, name = add_monster_check(args)
                        except Error as e:
                            writer.write(e.text.encode())
                            continue
                        await send_all(fun='addmon', args=game.add_monster(int(x), int(y), int(hp), hello, name))
                    case ['attack', args]:
                        try:
                            x, y = players[login].x, players[login].y
                            weapon, name = attack_check(args)
                            result = game.attack(x, y, int(weapon), name)
                            result['login'] = login
                            await send_all(fun = 'attack', args=result)
                        except Error as e:
                            writer.write(e.text.encode())
                    case ['move', args]:
                        d_x, d_y = [int(i) for i in args.split()]
                        writer.write(game.moving(players[login], d_x, d_y).encode())
                    case ['sendall', args]:
                        args = shlex.split(args)[0]
                        await send_all(mes="{login}: {args}", exception=players[login])
                    case ['movemonsters', args]:
                        try:
                            writer.write(game.set_mode(args).encode())
                        except Error as e:
                            writer.write(e.text.encode())
                    case ['locale', args]:
                        try:
                            writer.write(players[login].set_locale(args).encode())
                        except Error as e:
                            writer.write(e.text.encode())
            if request is receive:
                receive = asyncio.create_task(players[login].queue.get())
                writer.write(f"{request.result()}\n".encode())
                await writer.drain()

    send.cancel()
    receive.cancel()
    writer.close()
    del players[login]
    await send_all(fun='left', args={'login':login})
    await writer.wait_closed()


async def random_monster():
    """Generate wandering monster"""
    global game, players
    while True:
        if not game.mode:
            await asyncio.sleep(5)
            continue
        await asyncio.sleep(30)
        if game.monsters:
            moved = False
            while not moved and any(game.monsters.values()):
                try:
                    monster = game.monsters[random.choice(list(game.monsters.keys()))]
                    direction = random.choice([(0, 1, _('down')), (1, 0, _('right')), (0, -1, _('up')), (-1, 0, _('left'))])
                    x = (monster.x + direction[0]) % 10
                    y = (monster.y + direction[1]) % 10
                    if (x, y) not in game.monsters:
                        del game.monsters[(monster.x, monster.y)]
                        monster.x, monster.y = x, y
                        game.monsters[(monster.x, monster.y)] = monster
                        moved = True
                except AttributeError:
                    continue
            if moved:
                await send_all(_("{monster} moved one cell {direction}").format(monster = monster.cow,
                                                                            direction = direction[-1]))
                for i in players.values():
                    if i.x == x and i.y == y:
                        await i.queue.put(f"{game.encounter(x, y)}")


async def main():
    """Run server"""
    global game, players
    game = Game()
    players = {}
    server = await asyncio.start_server(echo, '0.0.0.0', 1337)
    asyncio.create_task(random_monster())
    async with server:
        await server.serve_forever()

def run_server():
    asyncio.run(main())
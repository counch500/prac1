import cmd
import shlex
import cowsay
import socket
import sys
import threading
import readline

class Error(Exception):
    def __init__(self, code, name=''):
        match code:
            case 1:
                self.text = "Invalid arguments"
            case 2:
                self.text = "Cannot add unknown monster"
            case 3:
                self.text = f"No {name} here"
            case 4:
                self.text = "Unknown weapon"

class Client_MUD(cmd.Cmd):
    prompt = 'MUD> '
    host = "localhost"
    port = 1337
    weapons = ["sword", "spear", "axe"]
    monster_list = cowsay.list_cows() + ["jgsbat"]

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.s.connect((self.host, self.port))
            self.s.sendall(f"{username}\n".encode())
            response = self.s.recv(1024).decode().strip()
            
            if response == "Username already taken":
                print("Это имя уже занято")
                return True
            elif response == "Username cannot contain spaces":
                print("Имя не должно содержать пробелов")
                return True
            
            print(response)
            
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()
            
        except ConnectionError:
            print("Не удалось подключиться к серверу")
            return True

    def receive_messages(self):
        while True:
            try:
                message = self.s.recv(4096).decode()
                if not message:
                    print("\nСоединение с сервером потеряно")
                    return True
                
                message = message.rstrip()
                if message:
                    current_input = readline.get_line_buffer()
                    sys.stdout.write(f"\r{message}\n{self.prompt}{current_input}")
                    sys.stdout.flush()
                    
            except ConnectionError:
                print("\nСоединение с сервером потеряно")
                return True
            except Exception as e:
                print(f"\nОшибка: {e}")
                return True

    def complete_addmon(self, text, line, begidx, endidx):
        words = shlex.split(line[:endidx])
    
    # Если только "addmon" и начали вводить (не завершили пробелом)
        if len(words) == 1 and not line.endswith(' '):
            return [c for c in self.monster_list if c.startswith(text)]
    
    # Если вводим название монстра (первый аргумент)
        if (len(words) == 1 and line.endswith(' ')) or (len(words) == 2 and not line.endswith(' ')):
            return [m for m in self.monster_list if m.startswith(text)]
    
    # Автодополнение параметров (hello, hp, coords)
        if len(words) >= 2 and words[-1] not in ['hello', 'hp', 'coords']:
            options = ['hello', 'hp', 'coords']
            return [o for o in options if o.startswith(text)]
    
    # Автодополнение значений параметров
        if len(words) >= 3:
            if words[-2] == 'coords' and len(words[-1]) < 2:
                return [str(i) for i in range(10) if str(i).startswith(text)]
            elif words[-2] == 'hp':
                return [str(i) for i in range(1, 100) if str(i).startswith(text)]
            elif words[-2] == 'hello':
                return ['"Hello!"' if '"Hello!"'.startswith(text) else text]
    
        return []

    def complete_attack(self, text, line, begidx, endidx):
        #words = (line[:endidx] + " ").split()
        words = shlex.split(line[:endidx], posix=False)
    # Разбиваем строку с учетом пробелов в кавычках
        raw_words = line[:endidx].split()

        if len(words) == 1 and not line.endswith(' '):
            return [m for m in self.monster_list if m.startswith(text)]
        # Автодополнение имени монстра
        if len(words) == 2:
            return [m for m in self.monster_list if m.startswith(text)]
                
        if (len(words) == 1 and line.endswith(' ')) or (len(words) == 2 and not line.endswith(' ')):
            return [m for m in self.monster_list if m.startswith(text)]
        # Автодополнение ключевого слова 'with'
        if len(words) == 3 and words[-1] == "with" and not line.endswith(' '):
            return []
    
    # Если ввели "attack монстр with " (пробел после with)
        if (len(raw_words) >= 3 and raw_words[-2] == "with" and line.endswith(' ')) or \
            (len(words) == 3 and line.endswith('with ')):
            return self.weapons
        elif len(words) == 3 and not line.endswith(' '):
            return ['with'] if 'with'.startswith(text) else []
        
        # Автодополнение оружия после 'with'
        elif len(words) >= 4 and words[-2] == 'with':
            return [w for w in self.weapons if w.startswith(text)]
        
        return []
    def do_addmon(self, args):
        try:
            x, y, hp, hello, name = self.add_monster_check(args)
            self.s.sendall(f"addmon {name} {x} {y} {hp} {hello}\n".encode())
        except Error as e:
            print(e.text)
        except ConnectionError:
            print("Соединение потеряно")
            return True

    def do_attack(self, args):
        try:
            weapon, name = self.attack_check(args)
            self.s.sendall(f"attack {weapon} {name}\n".encode())
        except Error as e:
            print(e.text)
        except ConnectionError:
            print("Соединение потеряно")
            return True

    def do_quit(self, arg):
        """Выйти из игры: quit"""
        print("Выход из игры...")
        self.s.close()
        return True

    def do_up(self, args):
        self.send_move(0, -1)

    def do_down(self, args):
        self.send_move(0, 1)

    def do_left(self, args):
        self.send_move(-1, 0)

    def do_right(self, args):
        self.send_move(1, 0)

    def send_move(self, dx, dy):
        try:
            self.s.sendall(f"move {dx} {dy}\n".encode())
        except ConnectionError:
            print("Соединение потеряно")
            return True

    def default(self, args):
        print("Неизвестная команда")

    def add_monster_check(self, args):
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
        if not all(v.isdigit() for v in [x, y, hp]):
            raise Error(1)
        x, y, hp = map(int, [x, y, hp])
        if not (0 <= x < 10 and 0 <= y < 10 and hp > 0):
            raise Error(1)
        if name not in self.monster_list:
            raise Error(2)
        return x, y, hp, hello, name

    def attack_check(self, args):
        splitted = shlex.split(args)
        parsed_args = parse_args(splitted, {'with': 1})
        if parsed_args:
            weapon = parsed_args["with"][0]
            if weapon not in self.weapons:
                raise Error(4)
        else:
            weapon = "sword"
        if not splitted or splitted[0] not in self.monster_list:
            raise Error(1)
        name = splitted[0]
        return weapon, name

def parse_args(args, param):
    args_parsed = {}
    for i in param:
        if i not in args:
            return None
        args_parsed[i] = args[args.index(i)+1 : args.index(i)+1+param[i]]
    return args_parsed

if __name__ == '__main__':
    print("<<< Welcome to Python-MUD 0.1 >>>")
    if len(sys.argv) < 2:
        print("Использование: python client.py <имя_пользователя>")
        sys.exit(1)
    
    client = Client_MUD(sys.argv[1])
    if client.cmdloop():
        sys.exit(1)

from . import *

if __name__ == '__main__':
    if len(sys.argv) > 3 and sys.argv[2] == '--file':
        file = open(sys.argv[3])
    else:
        file = None
    host = "localhost"
    port = 1337
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((host, port))
    s.sendall(f"{sys.argv[1]}\n".encode())
    if s.recv(1024).rstrip().decode() == '1':
        print("<<< Welcome to Python-MUD 0.1 >>>")
        print(f"Your login: {sys.argv[1]}")
        if file is None:
            cmdline = Client_MUD(socket=s)
        else:
            cmdline = Client_MUD(socket=s, stdin=file)
            cmdline.prompt = ''
            cmdline.use_rawinput = False
        mes = threading.Thread(target=cmdline.from_srv, args=(cmdline, s))
        mes.start()
        cmdline.cmdloop()
    else:
        print("ERROR: Choose another login")
    s.shutdown(socket.SHUT_RDWR)
    if file:
        file.close()

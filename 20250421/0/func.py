import math
import sys
import socket

def sqroots(coeffs: str) -> str:
    try:
        a, b, c = map(float, coeffs.split())
    except ValueError:
        raise ValueError("Неверный формат строки коэффициентов")

    if a == 0:
        raise ValueError("Коэффициент 'a' не может быть равен нулю")

    discriminant = b**2 - 4 * a * c

    if discriminant > 0:
        x1 = (-b + math.sqrt(discriminant)) / (2 * a)
        x2 = (-b - math.sqrt(discriminant)) / (2 * a)
        return f"{x1} {x2}"
    elif discriminant == 0:
        x = -b / (2 * a)
        return f"{x}"
    else:
        return ""


def sqrootnet(line, sock):
    sock.sendall((line + "\n").encode())
    return sock.recv(128).decode().strip()

if __name__ == "__main__":
    match sys.argv:
        case[prog, args]:
            print(sqroots(args))
        case[prog, args, host, port]:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, int(port)))
                print(sqrootnet(args, s))

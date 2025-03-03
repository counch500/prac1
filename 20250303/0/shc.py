import shlex
import readline

while s := input("command> ")
    print(shlex.join(shlex.split(s)))


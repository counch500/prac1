import shlex

fio = input("FIO: ")
loc = input("Mesto: ")
command = ['register', fio, loc]

result = shlex.join(command)

print(result)

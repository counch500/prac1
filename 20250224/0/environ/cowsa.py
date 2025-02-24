import cowsay
import sys

if "/" in sys.argv[2]:
    with open(sys.argv) as f:
        the_cow = cowsay.read_dot_cow(f)
        print(cowsay.cowsay(sys.argv[1], cowfile = the_cow))
else:
    print(cowsay.cowsay(sys.argv[1], sys.argv[2]))

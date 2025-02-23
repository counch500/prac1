import sys
from glob import iglob
from os.path import basename

if len(sys.argv) == 1:
    for branch in iglob('.git/refs/heads/*'):
        print(basename(branch))


import sys
from glob import iglob
from os.path import basename

def get_last_commit(branch):
    branch_path = f'.git/refs/heads/{branch}'
    with open(branch_path) as bp:
        return bp.readline().strip()

def view_commit(commit_id):
    commit_filepath = f'.git/objects/{commit_id[:2]}/{commit_id[2:]}'
    with open(commit_filepath, 'rb') as cf:
        obj = zlib.decompress(cf.read())
    obj_text = obj.decode()
    print(obj_text)

if len(sys.argv) == 1:
    for branch in iglob('.git/refs/heads/*'):
        print(basename(branch))
else:
    branch = sys.argv[1]
    last_commit = get_last_commit(branch)
    print("Последний коммит:", last_commit)
    view_commit(last_commit)

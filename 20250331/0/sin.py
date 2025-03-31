"""This is module."""
import sys
from math import *

def thefun(a, b, c):
    """This is function"""
    return int(a)/int(b) + sin(int(c))

l = sys.argv[1]
a = b = l
print(a, b, sin(int(l)))

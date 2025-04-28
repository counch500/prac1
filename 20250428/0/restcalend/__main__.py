from calendar import month
import sys

"""
mnth = int(sys.argv[1])
year = int(sys.argv[2]) if len(sys.argv) > 2 else 2025

cal = month(year, mnth).split("\n")
sep = "".join(c if c == " " else "=" for c in cal[1])
print(f".. table:: {cal[0]}\n\n   {sep}\n   {cal[1]}\n   {sep}")
print("\n".join("     " + line for line in cal[2:-1]))
print(f"    {sep}")
"""

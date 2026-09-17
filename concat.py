#!/bin/sh
''''exec "$(dirname "$0")/env/bin/python" "$0" "$@" # '''
# lines above let this be executed as a script but run with the virtual env! :D

###
## concatenates all texts into a single file
###

import os
import sys

ocwd = os.getcwd()
os.chdir(os.path.dirname(__file__))

DIVIDER = "================================================"

outpath = None
outputs: list[str] = []

if len(sys.argv) > 1:
    outpath = sys.argv[-1]

def check_and_append_file(fname: str, dir: str):
    fullpath = os.path.join(dir, fname)
    if not os.path.isfile(fullpath):
        return
    if fname.startswith(("_", ".")):
        return
    if not fname.endswith(".md"):
        return

    with open(fullpath, "r", encoding="utf-8") as infile:
        contents = infile.read()
        outputs.append(f"{DIVIDER}\n{fullpath}\n{DIVIDER}\n\n{contents}")

removals = [".git", "_scripts", "tmp", "notes"]

for root, dirs, files in os.walk("..", topdown=True):
    dirs.sort()
    if root == "..":
        for d in removals:
            if d in dirs:
                dirs.remove(d)
        continue
    for f in sorted(files):
        check_and_append_file(f, root)

for f in os.listdir(".."):
    check_and_append_file(f, "..")

if outpath != None:
    outpath = os.path.join(ocwd, outpath)
    outdir = os.path.dirname(outpath)

    os.makedirs(outdir, exist_ok=True)
    with open(outpath, "w") as outfile:
        _ = outfile.write("\n\n\n".join(outputs))
else:
    print("\n\n\n".join(outputs))

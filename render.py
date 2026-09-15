#!/bin/sh
''''exec "$(dirname "$0")/env/bin/python" "$0" "$@" # '''
# lines above let this be executed as a script but run with the virtual env! :D

###
## turns a markdown file into a preaching script (see the `template.typ` file for specifics)
###

import os
import subprocess
import sys

if len(sys.argv) < 2:
    sys.stderr.write("usage: render.py [file.md]")
    sys.exit(1)

filepath = os.path.abspath(sys.argv[1])
if not os.path.exists(filepath):
    sys.stderr.write(f"no such file: {filepath}")
    sys.exit(1)

os.chdir(os.path.dirname(__file__))

base = os.path.splitext(os.path.basename(filepath))[0]
fdir = os.path.dirname(filepath)

cmd = [
    "pandoc",
    "--from", "markdown",
    "--template", "./template.typ",
    "--to", "pdf",
    "--pdf-engine", "typst",
    "-o", os.path.join(fdir, f"{base}.pdf"),
    filepath
]

subprocess.check_call(cmd)

#!/bin/sh
''''exec "$(dirname "$0")/env/bin/python" "$0" "$@" # '''
# lines above let this be executed as a script but run with the virtual env! :D

###
## gives a word count of a given homily; use `--watch` to have it update whenever the file changes
##    time estimates are based on Shane's preaching speed; TODO: make this configurable
###

import os
import re
import sys
import time

watch = False
filepath = None

for arg in sys.argv[1:]:
    if arg == "--watch":
        watch = True
    elif filepath is None:
        filepath = arg
    else:
        sys.stderr.write("usage: wc.py [--watch] <file.md>\n")
        sys.exit(1)

if filepath is None:
    sys.stderr.write("usage: wc.py [--watch] <file.md>\n")
    sys.exit(1)


filepath = os.path.abspath(filepath)
if not os.path.exists(filepath):
    sys.stderr.write(f"no such file: {filepath}\n")
    sys.exit(1)

def report():
    if filepath is None:
        raise RuntimeError("can't report before filepath set")
    with open(filepath, "r", encoding="utf-8") as infile:
        contents = infile.read()

    m = re.match(r"^---\n.*?\n---\n?(.*)$", contents, flags=re.DOTALL)
    if m:
        text = m.group(1)
    else:
        text = contents

    text = text.strip()

    wc = len(text.split())

    # my preaching pace is around 130-140 wpm
    min_wpm = 140
    max_wpm = 130

    min_total_seconds = round(wc / min_wpm * 60)
    max_total_seconds = round(wc / max_wpm * 60)

    min_minutes, min_seconds_rem = divmod(min_total_seconds, 60)
    max_minutes, max_seconds_rem = divmod(max_total_seconds, 60)

    print(f"{filepath}:\n    {wc:,} words\n    Estimated time: {min_minutes}:{min_seconds_rem:02} ~ {max_minutes}:{max_seconds_rem:02}\n")


if not watch:
    report()
    sys.exit(0)


last_mtime = None

while True:
    try:
        mtime = os.path.getmtime(filepath)

        if mtime != last_mtime:
            last_mtime = mtime
            print("\033[2J\033[H", end="", flush=True)
            report()

        time.sleep(0.5)
    except KeyboardInterrupt:
        print()
        break

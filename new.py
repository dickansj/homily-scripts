#!/bin/sh
''''exec "$(dirname "$0")/env/bin/python" "$0" "$@" # '''
# lines above let this be executed as a script but run with the virtual env! :D

###
## creates a new homily file, letting you choose the date,
##   and pulling from the USCCB readings for that day
##   NB: USCCB website seems to not like this? sometimes it seems to lock us out.
###

import calendar
import os
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl

USCCB_WEB_TEMPLATE = "https://bible.usccb.org/bible/readings/%m%d%y.cfm"


os.chdir(os.path.join(os.path.dirname(__file__), ".."))

calendar.setfirstweekday(calendar.SUNDAY)

class DatePicker:
    def __init__(self):
        self.selected = date.today() # noqa: DTZ011
        self.control = FormattedTextControl(self.render)
        self.app: Application|None = None

    def render(self):
        d = self.selected
        cal = calendar.monthcalendar(d.year, d.month)
        month = calendar.month_name[d.month]

        out = []

        out.append(("bold", f"\n{month} {d.year}\n"))
        out.append(("bold", "Su Mo Tu We Th Fr Sa\n"))

        for week in cal:
            for day in week:
                if day == 0:
                    out.append(("", "   "))
                elif day == d.day:
                    out.append(("reverse", f"{day:2d} "))
                else:
                    out.append(("", f"{day:2d} "))
            out.append(("", "\n"))

        return out

picker = DatePicker()
kb = KeyBindings()

@kb.add("left")
def left_arrow(_):
    picker.selected -= timedelta(days=1)

@kb.add("right")
def right_arrow(_):
    picker.selected += timedelta(days=1)

@kb.add("up")
def up_arrow(_):
    picker.selected -= timedelta(days=7)

@kb.add("down")
def down_arrow(_):
    picker.selected += timedelta(days=7)

@kb.add("t")
def keypress_t(_):
    picker.selected = date.today() # noqa: DTZ011

@kb.add("enter")
def keypress_enter(event):
    event.app.exit(result=picker.selected)

@kb.add("c-c")
def ctrl_c(event):
    event.app.exit(result=None)

app = Application(
    layout=Layout(Window(content=picker.control)),
    key_bindings=kb,
    full_screen=False,
)

picker.app = app

target_date: date|None = app.run()

if not target_date:
    sys.stderr.write("No date selected!\n")
    sys.exit(1)


try:
    location = input("Location? (leave blank to copy most recent) > ")
except KeyboardInterrupt:
    print()
    raise SystemExit(130)

metadata = {
    "lectionary_number": "",
    "lectionary_string": "",
    "readings": "",
    "location": "",
    "date": target_date.strftime("%Y-%m-%d"),
}

output_file_path = f"./{metadata['date']}.md"
if os.path.exists(output_file_path):
    sys.stderr.write(f"Output file {output_file_path} already exists!\n")
    sys.exit(1)

if location == "":
    files = sorted([os.path.join(".", f) for f in os.listdir(".") if f.endswith(".md")])
    for root, _, filenames in os.walk("archive"):
        files.extend(
            os.path.join(root, f)
            for f in filenames
            if f.endswith(".md")
        )

    if len(files) > 0:
        most_recent = max(files, key=lambda p: os.path.basename(p))
        with open(most_recent, "r") as recent_file:
            content = recent_file.read()
        loc_match = re.search(r"^location: (.*)$", content, re.MULTILINE)
        if loc_match:
            metadata["location"] = loc_match.group(1)
else:
    metadata["location"] = location.strip()


err = False

print("Looking up readings from USCCB website...")

class ScrapingException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

url_req = target_date.strftime(USCCB_WEB_TEMPLATE)
dl_path = os.path.join("tmp", os.path.basename(url_req))
try:
    if not os.path.exists(dl_path):
        res = requests.get(url_req)
        if not res.ok:
            raise ScrapingException(f"couldn't fetch USCCB page @ {url_req} ({res})")
        else:
            with open(dl_path, "wb") as outfile:
                outfile.write(res.content)
    with open(dl_path, "r", encoding="utf-8") as dl_file:
        page = dl_file.read()
    soup = BeautifulSoup(page, features="html.parser")

    title_block = soup.select_one("div.b-lectionary div.innerblock")
    if not title_block:
        raise ScrapingException("no title block")
    header = title_block.select_one("h2")
    if not header:
        raise ScrapingException("no header in title block")
    metadata["lectionary_string"] = header.text.strip()
    lect_par = title_block.select_one("p")
    if not lect_par:
        raise ScrapingException("no lectionary paragraph in title block")
    lect_num = lect_par.text.strip().split(":")[-1].strip()
    if lect_num.isdigit():
        lect_num = int(lect_num)
    metadata["lectionary_number"] = lect_num

    readings = []
    verse_blocks = soup.select(".wr-block.b-verse")
    for block in verse_blocks:
        c_header = block.select_one(".content-header")
        if not c_header:
            raise ScrapingException("no header in one of the verse blocks")
        reading_header = c_header.select_one("h3.name")
        if not reading_header:
            raise ScrapingException("no reading label header in one of the verse blocks")
        reading_label = reading_header.text.strip()
        # The verse before the Gospel is labeled "Alleluia" most of the year and
        # "Verse Before the Gospel" in Lent; neither is a reading.
        if reading_label.lower() in ("alleluia", "verse before the gospel"):
            continue
        reading_address_link = c_header.select_one(".address a")
        if not reading_address_link:
            raise ScrapingException(f"no address found for {reading_label}")

        if reading_label.lower() == "or":
            readings[-1] += f" or {reading_address_link.text.strip()}"
        else:
            readings.append(reading_address_link.text.strip())
    metadata["readings"] = "; ".join(readings).replace(" ", " ")


except ScrapingException as exc:
    err = True
    sys.stderr.write(f"Scraping didn't work: {exc.message}\n")
    sys.stderr.write("Creating file with mostly blank metadata...\n")


with open(output_file_path, "w") as outfile:
    outfile.write(f"---\n{"\n".join([f'{k}: {v}' for k, v in metadata.items()])}\n---\n\n")

if os.path.exists(dl_path):
    os.unlink(dl_path)

if err:
    sys.exit(1)

print(f"✅ New homily created at {output_file_path}")

if os.environ.get("TERM_PROGRAM", "") == "vscode":
    code = shutil.which("code.cmd") or shutil.which("code")
    if code:
        print("📝 Opening file in VS Code...")
        subprocess.check_call([code, output_file_path])
    else:
        print("❌ Hmmm, couldn't figure out how to call VS Code.")
elif os.environ.get("ZED_TERM", "") == "true":
    zed = shutil.which("zed")
    if zed:
        print("📝 Opening file in Zed...")
        subprocess.check_call([zed, output_file_path])
    else:
        print("❌ Hmmm, couldn't figure out how to call Zed.")

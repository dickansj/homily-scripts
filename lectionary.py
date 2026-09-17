"""Readings keyed by lectionary number.

`liturgical.py` turns a date into a lectionary number; this turns the number
into the readings, from the tables Felix Just SJ publishes at
<https://catholic-resources.org/Lectionary/> -- the only public source keyed by
number rather than by date.

`fetch_lectionary.py` builds the table once, into tmp/lectionary/readings.json
under the preaching directory, and every lookup after that is local. The table
is not committed: it is someone else's compilation, fetched on demand.

    readings_for(number, year)   -> {"first": ..., "gospel": ...} or None
    readings_line(number, year)  -> "Isa 55:1-3; Ps 145:8-9, ...; Matt 14:13-21"

`year` is "I" or "II" (liturgical.ferial_year) and matters only for Ordinary
Time weekdays, where one number carries two first readings and one Gospel.
Citations are as the source spells them.
"""

import json
import os
import re

CACHE = os.path.join("tmp", "lectionary", "readings.json")   # under the preaching dir

_TABLE = None


def _load():
    global _TABLE
    if _TABLE is None:
        _TABLE = (json.load(open(CACHE, encoding="utf-8"))
                  if os.path.exists(CACHE) else {})
    return _TABLE


def available():
    """Whether the table has been fetched. Nothing here works without it."""
    return bool(_load())


# The source's placeholders where a row does not carry its own readings: a
# cross-reference to another page, or a note that the readings are chosen from
# a range of options (All Souls, ritual Masses). Neither is a citation.
PLACEHOLDER = re.compile(r"^\s*(\(|\[|\.\s*$|see\b)", re.I)


def is_placeholder(entry):
    """A row that names no readings of its own -- or names a menu of them.
    Two alternates ("Matt 10:17-22 or Luke 1:26-38") is an appointed choice;
    All Souls lists thirteen first readings, which is a list to choose from."""
    if not entry:
        return True
    for key in ("first", "gospel"):
        text = entry.get(key, "") or ""
        if PLACEHOLDER.match(text) or text.count(" or ") >= 3:
            return True
    return False


def readings_for(number, year=None):
    """The readings for a lectionary number, or None if the table cannot say.

    An Ordinary Time weekday number without a year is ambiguous rather than
    wrong, so it returns None instead of silently choosing one. A number whose
    readings are chosen from options returns None too: the choice is yours.
    """
    if number is None:
        return None
    entry = _load().get(str(number))
    if not entry:
        return None
    if isinstance(entry, dict) and {"I", "II"} & set(entry):
        entry = entry.get(year) if year in ("I", "II") else None
    return None if is_placeholder(entry) else entry


def readings_line(number, year=None):
    """The whole liturgy of the word, in the order it is proclaimed."""
    entry = readings_for(number, year)
    if not entry:
        return ""
    parts = [entry.get("first", ""), entry.get("psalm", ""),
             entry.get("second", ""), entry.get("gospel", "")]
    return "; ".join(p for p in parts if p)

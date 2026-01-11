import json
import sqlite3
from typing import Any
from files import Files
from models import Section
import math
import copy


def normalize_string(s: str):
    s = s.replace("\u00e9", "e").replace("é", "e")  #  removes é
    s = s.replace("\u00c9", "E").replace("É", "E")  #  removes É
    s = s.replace("\u00e8", "e").replace("è", "e")  #  removes è
    s = s.replace("\u00e2", "a").replace("â", "a")  #  removes â
    s = s.replace("\u00e7", "c").replace("ç", "c")  #  removes ç
    s = s.replace("\u00e0", "a").replace("à", "a")  #  removes à
    s = s.replace("\u0000", "")  #  removes null character

    return s


def handleViewData(targetClass: Section) -> Section:
    c = copy.deepcopy(targetClass)

    col = ["M", "T", "W", "R", "F"]
    row: list[int] = []

    for day in range(21):
        if day % 2 == 0:
            row.append(day * 50 + 800)
        else:
            row.append(math.floor(day / 2) * 2 * 50 + 830)

    days: dict[str, list[str]] = {}

    for leclab in targetClass.times:
        time = leclab.time

        for d, t in time.items():
            days.setdefault(d, []).extend(t)

    viewData: list[dict[str, list[int]]] = []

    for day in days:
        times = days[day]
        for t in times:
            t = t.split("-")

            try:
                rowStart = row.index(int(t[0])) + 1
            except ValueError:
                rowStart = 1

            try:
                rowEnd = row.index(int(t[1])) + 1
            except ValueError:
                rowEnd = 21

            for d in day:
                if d == "S":
                    continue

                colStart = col.index(d) + 1

                viewData.append({f"{colStart}": [rowStart, rowEnd]})

    c.view_data = viewData
    return c


def addViewData(files: Files):
    sections = files.get_parsed_sections_file_content()

    conn = sqlite3.connect(files.all_sections_final_path)
    cursor = conn.cursor()

    _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY,
            course TEXT,
            section_number TEXT,
            domain TEXT,
            code TEXT,
            more TEXT,
        );
    """)

    _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS times (
            id INTEGER PRIMARY KEY,
            section_id INTEGER,
            prof TEXT,
            title TEXT,
            type TEXT,
            time TEXT,
            FOREIGN KEY(section_id) REFERENCES sections(id)
        )
    """)

    for section in sections:
        pass

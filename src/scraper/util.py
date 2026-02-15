from sqlmodel import Session, inspect

from scraper.db import engine
from .files import Files
from .models import Section
import math


def normalize_string(s: str):
    s = s.replace("\u00e9", "e").replace("é", "e")  #  removes é
    s = s.replace("\u00c9", "E").replace("É", "E")  #  removes É
    s = s.replace("\u00e8", "e").replace("è", "e")  #  removes è
    s = s.replace("\u00e2", "a").replace("â", "a")  #  removes â
    s = s.replace("\u00e7", "c").replace("ç", "c")  #  removes ç
    s = s.replace("\u00e0", "a").replace("à", "a")  #  removes à
    s = s.replace("\u0000", "")  #  removes null character

    return s


def add_viewdata_to_section(targetClass: Section):
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

    targetClass.view_data = viewData


def save_sections_with_viewData(files: Files, force_override: bool = False):
    sections = files.get_parsed_sections_file_content()

    for section in sections:
        add_viewdata_to_section(section)

    insp = inspect(engine)

    if insp.has_table("section"):
        if not force_override:
            override = input("Sections table already exists, override? (y/n) ")
            if override.lower() != "y":
                return

    with Session(engine) as session:
        session.add_all(sections)
        session.add_all(section.times for section in sections)
        session.commit()

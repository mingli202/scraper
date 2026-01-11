import json
import sqlite3
from typing import Literal
from files import Files
from models import Section
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


def save_sections_with_viewData(files: Files):
    sections = files.get_parsed_sections_file_content()

    for section in sections:
        add_viewdata_to_section(section)

    conn = sqlite3.connect(files.all_sections_final_path)
    cursor = conn.cursor()

    if (
        cursor.execute(
            "SELECT name from sqlite_schema WHERE type='table' and tbl_name='sections'"
        ).fetchone()
        is not None
    ):
        override = input("Sections db already exists, override? (y/n) ")
        if override.lower() != "y":
            return

        _ = cursor.execute("DROP TABLE sections")
        _ = cursor.execute("DROP TABLE times")
        conn.commit()

    _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY,
            course TEXT,
            section_number TEXT,
            domain TEXT,
            code TEXT,
            more TEXT,
            view_data TEXT
        );
    """)

    _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS times (
            section_id INTEGER,
            prof TEXT,
            title TEXT,
            type TEXT,
            time TEXT,
            FOREIGN KEY(section_id) REFERENCES sections(id)
        )
    """)

    sections_to_insert: list[tuple[int, str, str, str, str, str, str]] = []
    times_to_insert: list[
        tuple[int, str, str, Literal["lecture", "laboratory"] | None, str]
    ] = []

    for section in sections:
        sections_to_insert.append(
            (
                section.id,
                section.course,
                section.section,
                section.domain,
                section.code,
                section.more,
                json.dumps(section.view_data),
            )
        )

        for leclab in section.times:
            times_to_insert.append(
                (
                    section.id,
                    leclab.prof,
                    leclab.title,
                    leclab.type,
                    json.dumps(leclab.time),
                )
            )

    _ = conn.executemany(
        """
        INSERT INTO sections values (?,?,?,?,?,?,?)
        """,
        sections_to_insert,
    )

    _ = conn.executemany(
        """
        INSERT INTO times values (?,?,?,?,?)
        """,
        times_to_insert,
    )

    conn.commit()
    conn.close()

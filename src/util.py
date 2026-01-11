import json
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


def addRating(files: Files):
    sections = files.get_parsed_sections_file_content()
    ratings = files.get_ratings_file_content()

    sections_with_rating: list[dict[str, Any]] = []

    for section in sections:
        for time in section.times:
            time.rating = ratings.get(time.prof)

        sections_with_rating.append(section.model_dump())

    with open(files.classes_file_path, "w") as file:
        _ = file.write(json.dumps(sections_with_rating, indent=2))


def handleViewData(targetClass: Section) -> dict:
    c = copy.deepcopy(targetClass)

    col = ["M", "T", "W", "R", "F"]
    row = []

    for day in range(21):
        if day % 2 == 0:
            row.append(day * 50 + 800)
        else:
            row.append(math.floor(day / 2) * 2 * 50 + 830)

    lecture = {}
    if targetClass.lecture:
        lecture = targetClass.lecture.time
    lab = {}
    if targetClass.lab:
        lab = targetClass.lab.time

    days = lecture | lab

    viewData = []

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
    return c.model_dump()


def addViewData(files: Files):
    classes = files.get_classes_file_content()

    polished: dict[int, dict] = {}
    for index, course in enumerate(classes):
        polished.update({index: handleViewData(course)})

    with open(files.all_classes_path, "w") as file:
        file.write(json.dumps(polished, indent=2))

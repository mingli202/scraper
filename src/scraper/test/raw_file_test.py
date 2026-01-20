import re
from typing import Callable, final
import unittest

from pydantic_core import from_json

from scraper.files import Files


class RawFileTest(unittest.TestCase):
    def setUp(self):
        self.cl = {}
        self.files = Files()

        self.raw: list[str] = []
        with open(self.files.raw_file, "r") as file:
            self.raw = from_json(file.read())

        self.classCodeRegex = r"\d{3}-\w{3}-\w{1,2}"

    def t(self, test_func: Callable[[str], bool]):
        print("TESTING", test_func.__name__)
        is_valid = True
        for i, row in enumerate(self.raw):
            if test_func(row):
                print(i, row, sep=": ")
                is_valid = False

        if not is_valid:
            raise

    def test_brokenDisc(self):
        self.t(self.brokenDisc)

    def test_time_doublelines(self):
        self.t(self.doublelines)

    # def test_time_duplicate(self):
    #     self.t(self.timeDuplicate)

    def test_lecture_line(self):
        self.t(self.lecture_line_not_starting_with_lecture)

    def brokenDisc(self, row: str):
        if re.search(r"[\w\d]+\s*Lecture", row) and not re.search(
            self.classCodeRegex, row
        ):
            return True

        if re.search(r"[\w\d]+\s*Laboratory", row) and not re.search(
            self.classCodeRegex, row
        ):
            return True

        if re.match(r"^\d{5}", row):
            if re.match(r"^\d{5}\s*\w+\d{3}-\w{3}-\w{1,2}", row):
                return True

        return False

    def doublelines(self, row: str):
        n = len(row) - len(row.lstrip())

        if n == 47:
            return True

        return False

    def timeDuplicate(self, row: str):
        if re.match(r"^\d{5}", row):
            self.cl = {}

            section, disc, code, *title, day, time = [
                k.replace("\x00", "") for k in row.split(" ") if k != ""
            ]

            self.cl["section"] = section
            self.cl["disc"] = disc
            self.cl["code"] = code
            self.cl["title"] = title
            self.cl[day] = time

        else:
            dayTime = re.search(r"([MTWRF])\s*(\d{4}-\d{4})", row)
            if dayTime:
                day = dayTime.group(1)
                time = dayTime.group(2)

                if day in self.cl:
                    return True
                else:
                    self.cl[day] = time

        return False

    def lecture_line_not_starting_with_lecture(self, row: str) -> bool:
        r = row.lstrip()

        return -1 < r.find("Lecture") < 0


"""
Some more edge cases:
- The line that contains the teacher doesn't have the word 'Lecture' before it
- Some classes have no teacher nor the word 'Lecture' in it wtf
"""

import pdfplumber
import pytest
import re

from files import Files
from models import Word
from new_parser import NewParser

files = Files()
with pdfplumber.open(files.pdf_path) as pdf:
    page = pdf.pages[0]
    print("width", page.width, "height", page.height)


@pytest.fixture
def parser():
    parser = NewParser(files)
    return parser


def test_correct_column_x(parser: NewParser):
    files = parser.files
    lines = files.get_sorted_lines_content()

    columns_x: dict[str, set[Word]] = {}

    for line in lines:
        first_word = line[0]
        line_text = " ".join([word.text for word in line])

        if first_word.text == "SECTION":
            assert len(line) == 7, line_text

            columns_x.setdefault("section", set()).add(first_word)
            columns_x.setdefault("disc", set()).add(line[1])
            columns_x.setdefault("course_number", set()).add(line[2])
            columns_x.setdefault("course_title", set()).add(line[5])
            continue

        if re.search(r"[MTWRF]{1,5}\s+\d{4}-\d{4}", line_text):
            assert len(line) >= 2, line_text

            day = line[-2]
            time = line[-1]

            columns_x.setdefault("day", set()).add(day)
            columns_x.setdefault("time", set()).add(time)

    assert len({s.x0 for s in columns_x["section"]}) == 1
    assert len({s.x0 for s in columns_x["disc"]}) == 1
    assert len({s.x0 for s in columns_x["course_number"]}) == 1
    assert len({s.x0 for s in columns_x["course_title"]}) == 1
    assert len({s.x0 for s in columns_x["day"]}) == 1, columns_x["day"]
    assert len({s.x0 for s in columns_x["time"]}) == 1

    assert columns_x["section"].pop().x0 == parser.columns_x.section
    assert columns_x["disc"].pop().x0 == parser.columns_x.disc
    assert columns_x["course_number"].pop().x0 == parser.columns_x.course_number
    assert columns_x["course_title"].pop().x0 == parser.columns_x.course_title
    assert columns_x["day"].pop().x0 == parser.columns_x.day
    assert columns_x["time"].pop().x0 == parser.columns_x.time


def test_basic_parsing(parser: NewParser):
    pass

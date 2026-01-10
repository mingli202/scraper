import pdfplumber
import pytest
import re

from files import Files
from models import LecLab, Section, Word
from new_parser import NewParser
from .individual_parsing_data import ATestCase, data

files = Files()
width, height = 0, 0

with pdfplumber.open(files.pdf_path) as pdf:
    page = pdf.pages[0]
    width = page.width
    height = page.height
    print("width", page.width, "height", page.height)


def get_word_position(word: Word) -> str:
    return f"word: {word.text}, page: {word.doctop / height:.0f}, top: {word.top / height:.2f}, x0: {word.x0 / width:.2f}"


@pytest.fixture
def parser():
    parser = NewParser(files)
    yield parser

    parser.sections = []
    parser.current_section = Section()
    parser.leclab = LecLab()


def test_optimal_x_tolerance() -> None:
    with pdfplumber.open(
        "/Users/vincentliu/Downloads/SCHEDULE_OF_CLASSES_Winter_2026_December_11.pdf"
    ) as pdf:
        page = pdf.pages[
            93
        ]  # this page contains (Blended)MW, which are very close to each other

        left = 1
        right = 3
        mid = 0

        for _ in range(0, 100):
            mid = (left + right) / 2
            words = page.extract_words(x_tolerance=mid)
            sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))

            for word in sorted_words[::-1]:
                if "(Blended)" in word["text"]:
                    if "MW" in word["text"]:
                        right = mid
                    else:
                        left = mid
                    break

        print("x_tolerance", mid)


def test_optmial_y_tolerance() -> None:
    with pdfplumber.open(
        "/Users/vincentliu/Downloads/SCHEDULE_OF_CLASSES_Winter_2026_December_11.pdf",
    ) as pdf:
        page = pdf.pages[115]

        left = 1
        right = 3
        mid = 0

        for _ in range(0, 100):
            mid = (left + right) / 2
            words = page.extract_words(y_tolerance=mid)
            sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))

            has_horlik = False
            for word in sorted_words[::-1]:
                if "Horlik" in word["text"]:
                    has_horlik = True
                    continue

                if has_horlik:
                    if "CERAMICS" in word["text"]:
                        right = mid
                    else:
                        left = mid
                    break

        print("y_tolerance", mid)


def test_correct_line_extraction(parser: NewParser) -> None:
    """
    Test to make sure the line extraction is correct: whether a word is well separated and the word text is correct

    Parameters:
        parser (NewParser): The parser object

    Examples cases that it should catch:
        - 00009 HUMA 345-101-MQ Settler Colonialism and Indigenous Resistance (Blended)MW 1230-1430
    """

    files = parser.files
    lines = files.get_sorted_lines_content()

    for line_y, line in lines.items():
        first_word = line[0]
        line_text = " ".join([word.text for word in line])

        if first_word.text == "SECTION":
            assert (
                line_text == "SECTION DISC COURSE NUMBER COURSE TITLE/TEACHER DAY/TIMES"
            ), "SECTION line should well separated"
            continue

        if re.match(r"^.*\d{4}-\d{4}$", line_text):
            assert len(line) >= 2, (line_y, line_text)

            day = line[-2]
            time = line[-1]

            assert re.match(r"^[MTWRF]+$", day.text) is not None, (
                "day should only contain letters M, T, W, R, F",
                line_text,
                get_word_position(day),
            )
            assert re.match(r"^\d{4}-\d{4}$", time.text) is not None, (
                "time should be in the format of HHMM-HHMM",
                line_text,
                get_word_position(time),
            )

            continue


def test_correct_column_x(parser: NewParser):
    files = parser.files
    lines = files.get_sorted_lines_content()

    columns_x: dict[str, set[Word]] = {}

    for line_y, line in lines.items():
        first_word = line[0]
        line_text = " ".join([word.text for word in line])

        if first_word.text == "SECTION":
            assert len(line) == 7, (line_y, line_text)

            columns_x.setdefault("section", set()).add(first_word)
            columns_x.setdefault("disc", set()).add(line[1])
            columns_x.setdefault("course_number", set()).add(line[2])
            columns_x.setdefault("course_title", set()).add(line[4])
            continue

        if re.match(r"^.*[MTWRF]{1,5} \d{4}-\d{4}$", line_text):
            assert len(line) >= 2, (line_y, line_text)

            day = line[-2]
            time = line[-1]

            columns_x.setdefault("day", set()).add(day)
            columns_x.setdefault("time", set()).add(time)

        if re.match(r"^\d{5}$", first_word.text):
            columns_x.setdefault("section", set()).add(first_word)
            columns_x.setdefault("disc", set()).add(line[1])

            code_index = next(
                i
                for i, w in enumerate(line)
                if re.match(r"^\d{3}-[A-Z0-9]{3}-[A-Z0-9]{1,2}$", w.text) is not None
            )

            columns_x.setdefault("course_number", set()).add(line[code_index])
            columns_x.setdefault("course_title", set()).add(line[code_index + 1])

        if any(
            line_text.startswith(s)
            for s in [
                "ADDITIONAL FEE",
                "Approximate materials",
                "***",
                "Lecture",
                "Laboratory",
                "For students in the old science program",
                "For Honours Science students only",
                "BLENDED LEARNING",
            ]
        ):
            columns_x.setdefault("course_number", set()).add(first_word)

    assert len({s.x0 for s in columns_x["section"]}) == 1
    assert len({s.x0 for s in columns_x["disc"]}) == 1

    for word in columns_x["course_number"]:
        if word.x0 == 130:
            print(get_word_position(word))

    assert len({s.x0 for s in columns_x["course_number"]}) == 1
    assert len({s.x0 for s in columns_x["course_title"]}) == 1
    assert len({s.x0 for s in columns_x["day"]}) == 1
    assert len({s.x0 for s in columns_x["time"]}) == 1

    assert columns_x["section"].pop().x0 == parser.columns_x.section
    assert columns_x["disc"].pop().x0 == parser.columns_x.disc
    assert columns_x["course_number"].pop().x0 == parser.columns_x.course_number
    assert columns_x["course_title"].pop().x0 == parser.columns_x.course_title
    assert columns_x["day"].pop().x0 == parser.columns_x.day
    assert columns_x["time"].pop().x0 == parser.columns_x.time


@pytest.mark.parametrize("test_case,expected", data)
def test_individual_parsing(parser: NewParser, test_case: ATestCase, expected: Section):
    print(test_case.name)
    parser.lines = test_case.lines
    parser.parse()

    assert len(parser.sections) == 1
    assert parser.sections[0] == expected.model_dump(by_alias=True)


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-v", __file__]))

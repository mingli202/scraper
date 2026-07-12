from collections import OrderedDict
import itertools
import json
from pathlib import Path
import re
from typing import Any

import pdfplumber
from pdfplumber.page import Page
from pydantic import TypeAdapter
from scraper.models import ColumnsXs, Word


def compute_sorted_lines_if_not_exist(
    sorted_lines_path: Path | None, pdf_path: Path
) -> OrderedDict[int, list[Word]]:
    """
    Gets the sorted lines at the given sorted_lines_path.
    If it exists and already parsed, return it, otherwise
    compute a fresh sorted_lines and save it
    """

    if sorted_lines_path is not None:
        if sorted_lines_path.exists():
            with open(sorted_lines_path, "r") as f:
                adapter = TypeAdapter(OrderedDict[int, list[Word]])
                return adapter.validate_json(f.read(), by_alias=True)

    sorted_lines = compute_sorted_lines(pdf_path)

    if sorted_lines_path is not None:
        save_sorted_lines(sorted_lines, sorted_lines_path)

    return sorted_lines


def save_sorted_lines(
    sorted_lines: OrderedDict[int, list[Word]], sorted_lines_path: Path
):
    """Saves the given sorted_lines as json to the given sorted_lines_path"""

    def map(word: Word) -> dict[str, Any]:
        return word.model_dump(by_alias=True)

    serializable_lines: OrderedDict[float, list[dict[str, Any]]] = OrderedDict()
    for k, v in sorted_lines.items():
        serializable_lines[k] = [map(w) for w in v]

    with open(sorted_lines_path, "w") as f:
        json.dump(serializable_lines, f, indent=2)


def compute_sorted_lines(pdf_path: Path) -> OrderedDict[int, list[Word]]:
    """
    Parses the pdf at the given path and returns an OrderedDict where
    the key is the y position of the line in the entire pdf and
    the value is a list of Word that makes up the line
    """
    lines: OrderedDict[int, list[Word]] = OrderedDict()

    with pdfplumber.open(pdf_path) as pdf:
        sorted_words = itertools.chain.from_iterable(
            __get_sorted_words(i, page) for i, page in enumerate(pdf.pages)
        )

        y = -1
        line: list[Word] = []
        for word in sorted_words:
            if word.doctop != y:
                if y != -1:
                    lines.update({y: line})
                    line = []
                y = word.doctop

            line.append(word)

        lines.update({y: line})

    return lines


def __get_sorted_words(page_number: int, page: Page) -> list[Word]:
    words = page.extract_words(x_tolerance=0.1, y_tolerance=0.1)

    sorted_words = sorted(
        (
            Word(
                text=re.sub(r"\(cid:\d+\)", "", word["text"]),
                x0=round(word["x0"]),
                doctop=round(word["doctop"]),
                top=round(word["top"]),
                page_number=page_number,
            )
            for word in words
        ),
        key=lambda w: (w.top, w.x0),
    )

    return [Word.model_validate(w, by_alias=True) for w in sorted_words]


def compute_columns_x(
    sorted_lines_dict: OrderedDict[int, list[Word]],
) -> ColumnsXs:
    # using the first class section to get all the columns
    columns_x_dict: dict[str, list[int]] = {}
    sorted_lines = list(sorted_lines_dict.values())
    i = 0
    while i < len(sorted_lines):
        line = sorted_lines[i]

        if line[0].text == "SECTION":
            break

        i += 1

    for word in sorted_lines[i]:
        text: str = word.text
        columns_x_dict.setdefault(text, []).append(word.x0)

    i += 1

    section_first_line = sorted_lines[i]

    assert re.match(r"\d{4}-\d{4}", section_first_line[-1].text)
    time_column = section_first_line[-1].x0

    assert re.match(r"[TMWRF]{1,5}", section_first_line[-2].text)
    day_column = section_first_line[-2].x0

    columns_x = ColumnsXs(
        section=columns_x_dict["SECTION"].pop(),
        disc=columns_x_dict["DISC"].pop(),
        day=day_column,
        time=time_column,
        course_number=columns_x_dict["COURSE"][0],
        course_title=columns_x_dict["COURSE"][1],
    )

    return columns_x

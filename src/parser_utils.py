from collections import OrderedDict
import itertools
from pathlib import Path
import re

import pdfplumber
from pdfplumber.page import Page
from models import ColumnsXs, Word


class ParserUtils:
    @staticmethod
    def compute_sorted_lines(pdf_path: Path) -> OrderedDict[float, list[Word]]:
        lines: OrderedDict[float, list[Word]] = OrderedDict()

        with pdfplumber.open(pdf_path) as pdf:
            sorted_words = itertools.chain.from_iterable(
                [ParserUtils.__get_sorted_words(page) for page in pdf.pages]
            )

            y = -1
            line: list[Word] = []
            for word in sorted_words:
                if word.doctop != y:
                    if y != -1:
                        lines.update({y: line})
                        line = []
                    y = round(word.doctop)

                line.append(word)

            lines.update({y: line})

        return lines

    @staticmethod
    def __get_sorted_words(page: Page) -> list[Word]:
        words = page.extract_words()

        for word in words:
            word["top"] = round(word["top"])
            word["doctop"] = round(word["doctop"])
            word["x0"] = round(word["x0"])

        sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))
        return [Word.model_validate(w, by_alias=True) for w in sorted_words]

    @staticmethod
    def compute_columns_x(
        sorted_lines_dict: OrderedDict[float, list[Word]],
    ) -> ColumnsXs:
        # using the first class section to get all the columns
        columns_x_dict: dict[str, list[float]] = {}
        sorted_lines = list(sorted_lines_dict.values())
        i = 0
        while i < len(sorted_lines):
            line = sorted_lines[i]

            if line[0].text == "SECTION":
                break

            i += 1

        for word in sorted_lines[i]:
            text: str = word.text
            columns_x_dict.setdefault(text, []).append(round(word.x0))

        i += 1

        section_first_line = sorted_lines[i]

        assert re.match(r"\d{4}-\d{4}", section_first_line[-1].text)
        time_column = round(section_first_line[-1].x0)

        assert re.match(r"[TMWRF]{1,5}", section_first_line[-2].text)
        day_column = round(section_first_line[-2].x0)

        columns_x = ColumnsXs(
            section=columns_x_dict["SECTION"].pop(),
            disc=columns_x_dict["DISC"].pop(),
            day=day_column,
            time=time_column,
            course_number=columns_x_dict["COURSE"][0],
            course_title=columns_x_dict["COURSE"][1],
        )

        return columns_x

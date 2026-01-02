from pathlib import Path
import re
from typing import Any

import pdfplumber
from pdfplumber.page import Page
from models import ColumnsXs


class ParserUtils:
    @staticmethod
    def compute_sorted_lines(pdf_path: Path) -> list[list[dict[str, Any]]]:
        lines: list[list[dict[str, Any]]] = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                sorted_words = ParserUtils.__get_sorted_words(page)

                line: list[dict[str, Any]] = []
                y = -1
                for word in sorted_words:
                    if word["top"] != y:
                        if y != -1:
                            lines.append(line)
                            line = []
                        y = word["top"]
                    line.append(word)
                lines.append(line)

        return lines

    @staticmethod
    def __get_sorted_words(page: Page):
        words = page.extract_words()

        for word in words:
            word["top"] = round(word["top"])

        sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))
        return sorted_words

    @staticmethod
    def compute_columns_x(sorted_lines: list[list[dict[str, Any]]]) -> ColumnsXs:
        # using the first class section to get all the columns
        columns_x_dict: dict[str, list[int]] = {}
        i = 0
        while i < len(sorted_lines):
            line = sorted_lines[i]

            if line[0]["text"] == "SECTION":
                break

            i += 1

        for word in sorted_lines[i]:
            text: str = word["text"]
            columns_x_dict.setdefault(text, []).append(word["x0"])

        i += 1

        section_first_line = sorted_lines[i]

        assert re.match(r"\d{4}-\d{4}", section_first_line[-1]["text"])
        time_column = section_first_line[-1]["x0"]

        assert re.match(r"[TMWRF]{1,5}", section_first_line[-2]["text"])
        day_column = section_first_line[-2]["x0"]

        columns_x = ColumnsXs(
            section=columns_x_dict["SECTION"].pop(),
            disc=columns_x_dict["DISC"].pop(),
            day=day_column,
            time=time_column,
            course_number=columns_x_dict["COURSE"][0],
            course_title=columns_x_dict["COURSE"][1],
        )

        return columns_x

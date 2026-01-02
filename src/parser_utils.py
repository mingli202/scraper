from pathlib import Path
from typing import Any

import pdfplumber
from pdfplumber.page import Page
from models import ColumnsXs


class ParserUtils:
    @staticmethod
    def compute_columns_x(sorted_lines: list[list[dict[str, Any]]]) -> ColumnsXs:
        columns_x_dict: dict[str, set[int]] = {}
        for line in sorted_lines:
            headers = [
                w
                for w in line
                if w["text"] in ["SECTION", "DISC", "COURSE", "DAY/TIMES"]
            ]

            for word in headers:
                text: str = word["text"]
                columns_x_dict.setdefault(text, set()).add(word["x0"])

        course_columns = sorted(list(columns_x_dict["COURSE"]))

        columns_x = ColumnsXs(
            section=columns_x_dict["SECTION"].pop(),
            disc=columns_x_dict["DISC"].pop(),
            day_times=columns_x_dict["DAY/TIMES"].pop(),
            course_number=course_columns[0],
            course_title=course_columns[1],
        )

        return columns_x

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

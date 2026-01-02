from dataclasses import dataclass
from functools import cache
from typing import Any, final

from pdfplumber.page import Page
from files import Files
import pdfplumber


@dataclass(frozen=True)
class ColumnsXs:
    SECTION: float = 0
    DISC: float = 0
    COURSE_NUMBER: float = 0
    COURSE_TITLE: float = 0
    DAY_TIMES: float = 0


@final
class NewParser:
    def __init__(self, files: Files):
        self.files = files
        self.columns_x: ColumnsXs = ColumnsXs()

    def setup_columns_x_coordinates(self):
        with pdfplumber.open(self.files.pdfFullPath) as pdf:
            columns_x: dict[str, set[int]] = {}
            for page in pdf.pages:
                sorted_words = self.get_sorted_words(page)
                headers = [
                    w
                    for w in sorted_words
                    if w["text"] in ["SECTION", "DISC", "COURSE", "DAY/TIMES"]
                ]

                for word in headers:
                    text: str = word["text"]
                    columns_x.setdefault(text, set()).add(word["x0"])

        course_coulmns = sorted(list(columns_x["COURSE"]))
        self.columns_x = ColumnsXs(
            SECTION=columns_x["SECTION"].pop(),
            DISC=columns_x["DISC"].pop(),
            DAY_TIMES=columns_x["DAY/TIMES"].pop(),
            COURSE_NUMBER=course_coulmns[0],
            COURSE_TITLE=course_coulmns[1],
        )

    def parse(self):
        with pdfplumber.open(self.files.pdfFullPath) as pdf:
            for page in pdf.pages:
                sorted_words = self.get_sorted_words(page)

                lines: list[list[dict[str, Any]]] = []
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

                for line in lines:
                    print(line)

    @cache
    def get_sorted_words(self, page: Page):
        words = page.extract_words()

        for word in words:
            word["top"] = round(word["top"])

        sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))
        return sorted_words


if __name__ == "__main__":
    files = Files()
    parser = NewParser(files)
    parser.setup_columns_x_coordinates()
    parser.parse()
    print(parser.columns_x)

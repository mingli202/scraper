from functools import cache
import json
from pathlib import Path
from typing import Any, final

import pdfplumber
from pdfplumber.page import Page
from pydantic import TypeAdapter
from pydantic_core import from_json

from models import ColumnsXs


@final
class Files:
    def __init__(self, pdf_path: Path | None = None) -> None:
        pwd = Path(__file__).parent.parent.resolve()

        if pdf_path is not None:
            self.pdf_path = pdf_path
        else:
            self.pdf_path = Path(
                "/Users/vincentliu/Downloads/SCHEDULE_OF_CLASSES_Winter_2026_December_11.pdf"
            )

        data_dir = pwd / "data" / self.pdf_path.stem
        data_dir.mkdir(exist_ok=True, parents=True)

        self.sorted_lines_path = data_dir / "sorted_lines.json"
        self.section_columns_x_path = data_dir / "section_columns_x.json"

    @cache
    def sorted_lines(self) -> list[list[dict[str, Any]]]:
        if self.sorted_lines_path.exists():
            with open(self.sorted_lines_path, "r") as f:
                adapter = TypeAdapter(list[list[dict[str, Any]]])
                return adapter.validate_json(from_json(f.read()))

        lines: list[list[dict[str, Any]]] = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                sorted_words = self.__get_sorted_words(page)

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

        with open(self.sorted_lines_path, "w") as f:
            json.dump(lines, f)

        return lines

    @cache
    def __get_sorted_words(self, page: Page):
        words = page.extract_words()

        for word in words:
            word["top"] = round(word["top"])

        sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))
        return sorted_words

    def get_section_columns_x(self) -> ColumnsXs:
        if self.section_columns_x_path.exists():
            with open(self.section_columns_x_path, "r") as f:
                return ColumnsXs.model_validate_json(from_json(f.read()))

        columns_x_dict: dict[str, set[int]] = {}
        for line in self.sorted_lines():
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

        with open(self.section_columns_x_path, "w") as f:
            json.dump(columns_x.model_dump_json(), f)

        return columns_x

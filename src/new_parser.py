from functools import cache
import json
from typing import Any, final

from pdfplumber.page import Page
from pydantic import BaseModel, TypeAdapter
from pydantic_core import from_json
from files import Files
import pdfplumber


class ColumnsXs(BaseModel):
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
        if self.files.section_columns_x_path.exists():
            with open(self.files.section_columns_x_path, "r") as f:
                self.columns_x = ColumnsXs.model_validate_json(from_json(f.read()))
                return

        columns_x_dict: dict[str, set[int]] = {}
        for line in self.get_sorted_lines():
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
            SECTION=columns_x_dict["SECTION"].pop(),
            DISC=columns_x_dict["DISC"].pop(),
            DAY_TIMES=columns_x_dict["DAY/TIMES"].pop(),
            COURSE_NUMBER=course_columns[0],
            COURSE_TITLE=course_columns[1],
        )
        with open(self.files.section_columns_x_path, "w") as f:
            json.dump(self.columns_x.model_dump_json(), f)

    def parse(self):
        lines = self.files.sorted_lines()


if __name__ == "__main__":
    files = Files()
    parser = NewParser(files)
    parser.setup_columns_x_coordinates()
    parser.parse()
    print(parser.columns_x)

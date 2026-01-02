from typing import Any, final

from files import Files
from models import ColumnsXs


@final
class NewParser:
    def __init__(self, files: Files):
        self.files = files
        self.columns_x = self.files.get_section_columns_x()

    def parse(self):
        lines = self.files.sorted_lines()


if __name__ == "__main__":
    files = Files()
    parser = NewParser(files)
    parser.parse()
    print(parser.columns_x)

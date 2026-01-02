from typing import Any, final

from files import Files


@final
class NewParser:
    def __init__(self, files: Files):
        self.files = files
        self.columns_x = self.files.get_section_columns_x_content()

    def parse(self):
        lines = self.files.get_sorted_lines_content()

        title = self.__get_line_text(lines[0])

        for line in lines[:2]:
            line_text = self.__get_line_text(line)
            print(line_text)

    def __get_line_text(self, line: list[dict[str, Any]]) -> str:
        return " ".join([word["text"] for word in line])


if __name__ == "__main__":
    files = Files()
    parser = NewParser(files)
    parser.parse()

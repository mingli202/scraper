import re
from typing import Any, final

from files import Files
from models import LecLab, Section, Word


@final
class NewParser:
    def __init__(self, files: Files):
        self.files = files
        self.columns_x = self.files.get_section_columns_x_content()

        self.sections: list[dict[str, Any]] = []
        self.section: Section = Section()
        self.tmp: LecLab | None = None

    def __get_line_text(self, line: list[Word]) -> str:
        return " ".join([word.text for word in line])

    def parse(self):
        lines = self.files.get_sorted_lines_content()

        title = self.__get_line_text(lines[0])

        i = 0

        while i < len(lines):
            line = lines[i]
            line_text = self.__get_line_text(line)

            if re.match(r"John Abbott College \d{1,3}", line_text):
                continue

            if line_text == title:
                i += 1
                section_type = self.__get_line_text(lines[i])

                if section_type != self.section.type:
                    self.__update_section()
                    self.section = Section()

                self.section.type = section_type
                continue

            self.__parse_line(lines[i])

            i += 1

    def __update_section(self):
        if self.section.section == "":
            return

        self.sections.append(self.section.model_dump(by_alias=True))

        self.section.count += 1
        self.section.section = ""
        self.section.code = ""
        self.section.lecture = None
        self.section.lab = None
        self.section.more = ""
        self.section.view_data = []

    def __parse_line(self, line: list[Word]):
        section = self.section

        for i, word in enumerate(line):
            x = word.x0
            text = word.text

            if self.columns_x.section == x:
                if re.match(r"\d{5}", text):
                    self.__update_section()
                    section.section = text
                else:
                    section.course = text
                continue

            if self.columns_x.disc == x:
                continue

            if self.columns_x.course_number == x:
                if text == "Lecture" or text == "Laboratory":
                    section.lecture = LecLab()
                elif re.match(r"\d{3}-[A-Z0-9]{3}-[A-Z0-9]{1,2}", text):
                    section.code = text
                else:
                    section.more = self.__get_line_text(line)

                    if re.match("^ADDITIONAL", text) or re.match(
                        r"\*\*\*.*\*\*\*", text
                    ):
                        section.more += "\n"

            if self.columns_x.course_title <= x < self.columns_x.day:
                leclab = section.lecture
                assert leclab is not None, "Lecture word should be parsed first"

                if section.lab is not None:
                    leclab = section.lab

                continue

            if self.columns_x.day == x:
                section.lab = section.lab or LecLab()
                section.lab.update(section.lab)
                section.lab.time.setdefault(text, []).append(x)
                continue


if __name__ == "__main__":
    files = Files()
    parser = NewParser(files)
    parser.parse()

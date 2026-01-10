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
        self.current_section: Section = Section()
        self.current_section_time: LecLab = LecLab()
        self.lines = self.files.get_sorted_lines_content()

    def __get_line_text(self, line: list[Word]) -> str:
        return " ".join([word.text for word in line])

    def parse(self):
        lines = self.lines

        title = self.__get_line_text(lines[0])

        i = 0
        complementary_rules = False

        while i < len(lines):
            line = lines[i]
            line_text = self.__get_line_text(line)

            if re.match(
                r"John Abbott College \d{1,3}",
                line_text,  # footer
            ) or line_text.startswith("SECTION"):  # column header
                continue

            if line_text == "COMPLEMENTARY RULES":
                complementary_rules = True

            if complementary_rules:
                if line_text == title:
                    complementary_rules = False

                continue

            if line_text == title:
                i += 1
                section_type = self.__get_line_text(lines[i])

                if section_type != self.current_section.type:
                    self.__update_section()
                    self.current_section = Section()

                self.current_section.type = section_type
                continue

            self.__parse_line(lines[i])

            i += 1

        self.__update_section()

    def __update_section(self):
        if self.current_section.section == "":
            return

        title_lines = self.current_section_time.title.split(";")

        if len(title_lines) > 1:
            prof = title_lines[-1]
            self.current_section_time.prof = prof
            self.current_section_time.title = " ".join(title_lines[:-1])

        self.current_section.times.append(self.current_section_time)

        self.sections.append(self.current_section.model_dump(by_alias=True))

        self.current_section.count += 1
        self.current_section.section = ""
        self.current_section.code = ""
        self.current_section.times = []
        self.current_section.more = ""
        self.current_section.view_data = []
        self.current_section_time.clear()

    def __parse_line(self, line: list[Word]):
        section = self.current_section

        did_update_title = False

        for i, word in enumerate(line):
            x = word.x0
            text = word.text

            if self.columns_x.section == x:
                if re.match(r"^\d{5}$", text):
                    self.__update_section()
                    section.section = text
                else:
                    if section.course != text:
                        self.__update_section()
                    section.course = text
                continue

            if self.columns_x.disc == x:
                continue

            if self.columns_x.course_number == x:
                if text == "Lecture" or text == "Laboratory":
                    continue
                elif re.match(r"^\d{3}-[A-Z0-9]{3}-[A-Z0-9]{1,2}$", text):
                    section.code = text
                else:
                    section.more = self.__get_line_text(line)

                    if re.match("^ADDITIONAL", text) or re.match(
                        r"\*\*\*.*\*\*\*", text
                    ):
                        section.more += "\n"
                continue

            if self.columns_x.course_title <= x < self.columns_x.day:
                self.current_section_time.title += text + " "
                did_update_title = True
                continue

            if self.columns_x.day == x:
                day = text
                time = line[i + 1].text

                self.current_section_time.update_time({day: [time]})
                continue

        if did_update_title:
            self.current_section_time.title += ";"


if __name__ == "__main__":
    files = Files()
    parser = NewParser(files)
    # parser.parse()

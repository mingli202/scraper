import logging
import re
from typing import Any, final


from files import Files
from models import LecLab, Section, Word

logger = logging.getLogger(__name__)


@final
class NewParser:
    def __init__(self, files: Files):
        self.files = files
        self.columns_x = self.files.get_section_columns_x_content()

        self.sections: list[dict[str, Any]] = []
        self.current_section: Section = Section()
        self.leclab: LecLab = LecLab()
        self.lines = self.files.get_sorted_lines_content()

    def __get_line_text(self, line: list[Word]) -> str:
        return " ".join([word.text for word in line])

    def parse(self):
        lines = list(self.lines.values())

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

                if section_type != self.current_section.course_type:
                    self.__update_section()
                    self.current_section = Section()

                self.current_section.course_type = section_type
                continue

            self.__parse_line(lines[i])

            i += 1

        self.__update_section()

    def __update_section(self):
        if self.current_section.section == "":
            return

        self.__update_section_times()

        self.current_section.more = self.current_section.more.strip("\n")
        self.sections.append(self.current_section.model_dump(by_alias=True))

        self.current_section.count += 1
        self.current_section.section = ""
        self.current_section.code = ""
        self.current_section.times = []
        self.current_section.more = ""
        self.current_section.view_data = []

    def __update_section_times(self):
        if self.leclab.title == "":
            return

        self.leclab.title = self.leclab.title.strip(";")
        title_lines = self.leclab.title.split(";")
        title_lines = [line.strip() for line in title_lines]

        updated_title = False

        if len(title_lines) > 1 and self.leclab.prof == "" and self.leclab.type is None:
            logger.info("no 'Lecture' keyword")

            prof = title_lines[-1]

            if prof.startswith("TBA-") or re.match(r"^([A-Z].+), ([A-Z].+)$", prof):
                logger.info(f"{prof} is valid")

                self.leclab.prof = prof
                self.leclab.title = " ".join(title_lines[:-1])
                updated_title = True

        if not updated_title:
            self.leclab.title = " ".join(title_lines)

        self.current_section.times.append(self.leclab.__deepcopy__())
        self.leclab.clear()

    def __parse_line(self, line: list[Word]):
        section = self.current_section

        did_update_title = False
        is_leclab_line = False

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
                if "Lecture" in text:
                    is_leclab_line = True
                    self.leclab.type = "lecture"
                elif "Laboratory" in text:
                    is_leclab_line = True
                    self.leclab.type = "laboratory"
                continue

            if self.columns_x.course_number == x:
                if "Lecture" == text:
                    is_leclab_line = True
                    self.leclab.type = "lecture"
                    continue
                elif "Laboratory" == text:
                    is_leclab_line = True
                    self.leclab.type = "laboratory"
                    continue
                elif re.match(r"^\d{3}-[A-Z0-9]{3}-[A-Z0-9]{1,2}$", text):
                    self.__update_section_times()
                    section.code = text
                else:
                    section.more = self.__get_line_text(line)

                    if re.match("^ADDITIONAL", text) or re.match(
                        r"\*\*\*.*\*\*\*", text
                    ):
                        section.more += "\n"
                continue

            if self.columns_x.course_title <= x < self.columns_x.day:
                if is_leclab_line:
                    self.leclab.prof += text + " "
                else:
                    self.leclab.title += text + " "
                    did_update_title = True
                continue

            if self.columns_x.day == x:
                day = text
                time = line[i + 1].text

                self.leclab.update_time({day: [time]})
                continue

        if did_update_title:
            self.leclab.title = self.leclab.title.strip()
            self.leclab.title += ";"

        if is_leclab_line:
            self.leclab.prof = self.leclab.prof.strip()


if __name__ == "__main__":
    files = Files()
    parser = NewParser(files)
    # parser.parse()

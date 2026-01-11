import json
import logging
import re
from typing import Any, final, override
from abc import ABC, abstractmethod


from files import Files
from models import LecLab, Section, Word

logger = logging.getLogger(__name__)


class INewParser(ABC):
    def run(self):
        self.parse()
        self.cache_sections()

    @abstractmethod
    def parse(self):
        pass

    @abstractmethod
    def cache_sections(self):
        pass


@final
class NewParser(INewParser):
    def __init__(self, files: Files):
        self.files = files
        self.columns_x = self.files.get_section_columns_x_content()

        self.sections: list[dict[str, Any]] = []
        self.current_section: Section = Section()
        self.leclab: LecLab = LecLab()
        self.lines = self.files.get_sorted_lines_content()

    @override
    def parse(self, use_cache: bool = True):
        if use_cache and self.files.parsed_sections_path.exists():
            with open(self.files.parsed_sections_path, "r") as file:
                self.sections = json.loads(file.read())
            return

        lines = list(self.lines.values())

        title = self._get_line_text(lines[0])

        i = 0
        complementary_rules = False

        while i < len(lines):
            line = lines[i]
            i += 1
            line_text = self._get_line_text(line)

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
                else:
                    continue

            if line_text == title:
                section_type = self._get_line_text(lines[i])
                i += 1

                if section_type != self.current_section.course:
                    self._update_section()
                    self.current_section.course = ""
                    self.current_section.domain = ""

                self.current_section.course = section_type
                continue

            self._parse_line(line)

        self._update_section()

    def _parse_line(self, line: list[Word]):
        section = self.current_section

        did_update_title = False
        is_leclab_line = False

        for i, word in enumerate(line):
            x = word.x0
            text = word.text

            if self.columns_x.section <= x < self.columns_x.disc:
                if x != self.columns_x.section:
                    return

                if re.match(r"^\d{5}$", text):
                    self._update_section()
                    section.section = text
                else:
                    line_text = self._get_line_text(line)
                    if section.domain != line_text:
                        self._update_section()
                    section.domain = line_text
                continue

            if self.columns_x.disc == x:
                if "Lecture" in text:
                    logger.info("lecture in disc")
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
                    self._update_section_times()
                    section.code = text
                else:
                    section.more += self._get_line_text(line)

                    if re.match("^ADDITIONAL", text) or re.match(
                        r"\*\*\*.*\*\*\*", text
                    ):
                        section.more += "\n"
                    else:
                        section.more += " "

                    return
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

    def _get_line_text(self, line: list[Word]) -> str:
        return " ".join([word.text for word in line])

    def _update_section(self):
        if self.current_section.section == "":
            return

        self._update_section_times()

        self.current_section.more = self.current_section.more.strip("\n").strip()
        self.sections.append(self.current_section.model_dump(by_alias=True))

        self.current_section.id += 1
        self.current_section.section = ""
        self.current_section.code = ""
        self.current_section.times = []
        self.current_section.more = ""
        self.current_section.view_data = []

    def _update_section_times(self):
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

    @override
    def cache_sections(self):
        if self.files.parsed_sections_path.exists():
            return

        with open(self.files.parsed_sections_path, "w") as file:
            _ = file.write(json.dumps(self.sections, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    files = Files()
    parser = NewParser(files)
    parser.parse()
    parser.cache_sections()

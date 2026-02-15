import json
import logging
import math
import re
from typing import final, override
from abc import ABC, abstractmethod

from sqlmodel import SQLModel, Session, text

from .db import engine


from .files import Files
from .models import LecLab, LecLabType, Section, Word

logger = logging.getLogger(__name__)


class INewParser(ABC):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def parse(self):
        pass

    @abstractmethod
    def save_sections(self):
        pass


@final
class NewParser(INewParser):
    def __init__(self, files: Files):
        self.files = files
        self.columns_x = self.files.get_section_columns_x_content()

        self.sections: list[Section] = []
        self.current_section: Section = Section()
        self.leclab: LecLab = LecLab()
        self.lines = self.files.get_sorted_lines_content()

    @override
    def run(self, force_override: bool = False):
        if not force_override and self.files.parsed_sections_path.exists():
            override = input("Pdf already parsed, override? (y/n): ")

            if override.lower() != "y":
                with open(self.files.parsed_sections_path, "r") as file:
                    self.sections = json.loads(file.read())
                return

        self.parse()
        self.save_sections()

    @override
    def parse(self):
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
                    self.leclab.type = LecLabType.LECTURE
                elif "Laboratory" in text:
                    is_leclab_line = True
                    self.leclab.type = LecLabType.LAB
                continue

            if self.columns_x.course_number == x:
                if "Lecture" == text:
                    is_leclab_line = True
                    self.leclab.type = LecLabType.LECTURE
                    continue
                elif "Laboratory" == text:
                    is_leclab_line = True
                    self.leclab.type = LecLabType.LAB
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

        title = next(
            leclab.title for leclab in self.current_section.times if leclab.title != ""
        )

        self.current_section.title = title

        self.current_section.more = self.current_section.more.strip("\n").strip()
        self._add_viewdata_to_current_section()

        self.sections.append(self.current_section)

        self.current_section = Section(
            course=self.current_section.course,
            domain=self.current_section.domain,
        )

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

        self.leclab.section_id = self.current_section.id
        self.current_section.times.append(self.leclab)
        self.leclab = LecLab()

    def _add_viewdata_to_current_section(self):
        col = ["M", "T", "W", "R", "F"]
        row: list[int] = []

        for day in range(21):
            if day % 2 == 0:
                row.append(day * 50 + 800)
            else:
                row.append(math.floor(day / 2) * 2 * 50 + 830)

        days: dict[str, list[str]] = {}

        for leclab in self.current_section.times:
            time = leclab.time

            for d, t in time.items():
                days.setdefault(d, []).extend(t)

        viewData: list[dict[str, list[int]]] = []

        for day in days:
            times = days[day]
            for t in times:
                t = t.split("-")

                try:
                    rowStart = row.index(int(t[0])) + 1
                except ValueError:
                    rowStart = 1

                try:
                    rowEnd = row.index(int(t[1])) + 1
                except ValueError:
                    rowEnd = 21

                for d in day:
                    if d == "S":
                        continue

                    colStart = col.index(d) + 1

                    viewData.append({f"{colStart}": [rowStart, rowEnd]})

        self.current_section.view_data = viewData

    @override
    def save_sections(self):
        with Session(engine) as session:
            session.add_all(self.sections)
            session.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    files = Files()
    parser = NewParser(files)
    parser.parse()
    parser.save_sections()

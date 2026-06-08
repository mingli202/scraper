import logging
import math
import re
import json
from typing import final, override
from abc import ABC, abstractmethod

from pydantic import TypeAdapter

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
        if not force_override and self.files.all_sections_final_path_json.exists():
            with open(self.files.all_sections_final_path_json, "r") as file:
                try:
                    existing_sections = TypeAdapter(list[Section]).validate_json(
                        file.read()
                    )
                    if existing_sections:
                        override = input(
                            "Sections JSON already populated, override? (y/n): "
                        )

                        if override.lower() != "y":
                            return
                except Exception:
                    pass

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
                    self._update_section(False)

                self.current_section.course = section_type
                continue

            self._parse_line(line)

        self._update_section()

    def _parse_line(self, line: list[Word]):
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
                    self.current_section.section = text
                else:
                    line_text = self._get_line_text(line)
                    if self.current_section.domain != line_text:
                        self._update_section()
                    self.current_section.domain = line_text
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
                    self.current_section.code = text
                else:
                    self.current_section.more += self._get_line_text(line)

                    if re.match("^ADDITIONAL", text) or re.match(
                        r"\*\*\*.*\*\*\*", text
                    ):
                        self.current_section.more += "\n"
                    else:
                        self.current_section.more += " "

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
                start, end = time.split("-")

                self.leclab.update_time(day, start, end)
                continue

        if did_update_title:
            self.leclab.title = self.leclab.title.strip()
            self.leclab.title += ";"

        if is_leclab_line:
            self.leclab.prof = self.leclab.prof.strip()

    def _get_line_text(self, line: list[Word]) -> str:
        return " ".join([word.text for word in line])

    def _update_section(self, keep_course: bool = True):
        if self.current_section.section == "":
            return

        self._update_section_times()

        self.current_section.more = self.current_section.more.strip("\n").strip()
        self._add_viewdata_to_current_section()

        self.sections.append(self.current_section)

        new_id = f"{self.current_section.code}-{self.current_section.section}"

        if keep_course:
            self.current_section = Section(
                id=new_id,
                course=self.current_section.course,
                domain=self.current_section.domain,
            )
        else:
            self.current_section = Section(
                id=new_id,
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

        self.current_section.title = self.leclab.title

        self.current_section.leclabs.append(self.leclab)

        self.leclab = LecLab()

    def _add_viewdata_to_current_section(self):
        col = ["M", "T", "W", "R", "F"]
        row: list[int] = []

        for day in range(21):
            if day % 2 == 0:
                row.append(day * 50 + 800)
            else:
                row.append(math.floor(day / 2) * 2 * 50 + 830)

        days: dict[str, list[tuple[str, str]]] = {}

        for leclab in self.current_section.leclabs:
            for day_time in leclab.day_times:
                days.setdefault(day_time.day, []).append(
                    (day_time.start_time_hhmm, day_time.end_time_hhmm)
                )

        viewData: list[dict[str, list[int]]] = []

        for day in days:
            times = days[day]
            for t in times:
                start_time, end_time = t
                try:
                    rowStart = row.index(int(start_time)) + 1
                except ValueError:
                    rowStart = 1

                try:
                    rowEnd = row.index(int(end_time)) + 1
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
        with open(self.files.all_sections_final_path_json, "w") as file:
            _ = file.write(
                json.dumps(
                    [
                        section.model_dump(mode="json", by_alias=True)
                        for section in self.sections
                    ],
                    indent=2,
                )
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    files = Files()
    parser = NewParser(files)
    parser.parse()
    parser.save_sections()

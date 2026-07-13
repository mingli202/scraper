import logging
import math
from pathlib import Path
import re
import json
from typing import final

from pydantic import TypeAdapter

from scraper.files import Files
from scraper.models import ColumnsXs, LecLab, LecLabType, Section, Word
from scraper.parser_utils import compute_columns_x, compute_sorted_lines
from scraper.util import contains_data

logger = logging.getLogger(__name__)


@final
class NewParser:
    def __init__(self):
        self._sections: list[Section] = []
        self._current_section: Section = Section()
        self._leclab: LecLab = LecLab()

    def parse(self, lines: list[list[Word]], columns_x: ColumnsXs) -> list[Section]:
        """
        Parses the given lines and returns the list of Sections that got parsed
        """
        title = get_line_text(lines[0])

        i = 0
        complementary_rules = False

        while i < len(lines):
            line = lines[i]
            i += 1
            line_text = get_line_text(line)

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
                section_type = get_line_text(lines[i])
                i += 1

                if section_type != self._current_section.course:
                    self._update_section(False)

                self._current_section.course = section_type
                continue

            self._parse_line(line, columns_x)

        self._update_section()

        return self._sections

    def _parse_line(self, line: list[Word], columns_x: ColumnsXs):
        did_update_title = False
        is_leclab_line = False

        for i, word in enumerate(line):
            x = word.x0
            text = word.text

            if columns_x.section <= x < columns_x.disc:
                if x != columns_x.section:
                    return

                if re.match(r"^\d{5}$", text):
                    self._update_section()
                    self._current_section.section = text
                else:
                    line_text = get_line_text(line)
                    if self._current_section.domain != line_text:
                        self._update_section()
                    self._current_section.domain = line_text
                continue

            if columns_x.disc == x:
                if "Lecture" in text:
                    logger.info("lecture in disc")
                    is_leclab_line = True
                    self._leclab.type = LecLabType.LECTURE
                elif "Laboratory" in text:
                    is_leclab_line = True
                    self._leclab.type = LecLabType.LAB
                continue

            if columns_x.course_number == x:
                if "Lecture" == text:
                    is_leclab_line = True
                    self._leclab.type = LecLabType.LECTURE
                    continue
                elif "Laboratory" == text:
                    is_leclab_line = True
                    self._leclab.type = LecLabType.LAB
                    continue
                elif re.match(r"^\d{3}-[A-Z0-9]{3}-[A-Z0-9]{1,2}$", text):
                    self._update_section_times()
                    self._current_section.code = text
                else:
                    self._current_section.more += get_line_text(line)

                    if re.match("^ADDITIONAL", text) or re.match(
                        r"\*\*\*.*\*\*\*", text
                    ):
                        self._current_section.more += "\n"
                    else:
                        self._current_section.more += " "

                    return
                continue

            if columns_x.course_title <= x < columns_x.day:
                if is_leclab_line:
                    self._leclab.prof += text + " "
                else:
                    self._leclab.title += text + " "
                    did_update_title = True
                continue

            if columns_x.day == x:
                day = text
                time = line[i + 1].text
                start, end = time.split("-")

                self._leclab.update_time(day, start, end)
                continue

        if did_update_title:
            self._leclab.title = self._leclab.title.strip()
            self._leclab.title += ";"

        if is_leclab_line:
            self._leclab.prof = self._leclab.prof.strip()

    def _update_section(self, keep_course: bool = True):
        if self._current_section.section == "":
            return

        self._update_section_times()

        self._current_section.more = self._current_section.more.strip("\n").strip()
        self._add_viewdata_to_current_section()

        id = f"{self._current_section.code}-{self._current_section.section}"
        self._current_section.id = id

        self._sections.append(self._current_section)

        if keep_course:
            self._current_section = Section(
                course=self._current_section.course,
                domain=self._current_section.domain,
            )
        else:
            self._current_section = Section()

    def _update_section_times(self):
        if self._leclab.title == "":
            return

        self._leclab.title = self._leclab.title.strip(";")
        title_lines = self._leclab.title.split(";")
        title_lines = [line.strip() for line in title_lines]

        updated_title = False

        if (
            len(title_lines) > 1
            and self._leclab.prof == ""
            and self._leclab.type is None
        ):
            logger.info("no 'Lecture' keyword")

            prof = title_lines[-1]

            if prof.startswith("TBA-") or re.match(r"^([A-Z].+), ([A-Z].+)$", prof):
                logger.info(f"{prof} is valid")

                self._leclab.prof = prof
                self._leclab.title = " ".join(title_lines[:-1])
                updated_title = True

        if not updated_title:
            self._leclab.title = " ".join(title_lines)

        self._current_section.title = self._leclab.title

        self._current_section.leclabs.append(self._leclab)

        self._leclab = LecLab()

    def _add_viewdata_to_current_section(self):
        col = ["M", "T", "W", "R", "F"]
        row: list[int] = []

        for day in range(21):
            if day % 2 == 0:
                row.append(day * 50 + 800)
            else:
                row.append(math.floor(day / 2) * 2 * 50 + 830)

        days: dict[str, list[tuple[str, str]]] = {}

        for leclab in self._current_section.leclabs:
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

        self._current_section.view_data = viewData


def get_line_text(line: list[Word]) -> str:
    """
    Gets the str representation of the given list of Words
    """
    return " ".join([word.text for word in line])


def check_if_already_parsed(files: Files | None) -> list[Section] | None:
    """
    Checks if the sections are already parsed and saved.
    If so, asks the user if they want to override
    """
    if files is None:
        return None

    if files.parsed_sections_path.exists():
        with open(files.parsed_sections_path, "r") as file:
            existing_sections = TypeAdapter(list[Section]).validate_json(file.read())
            if existing_sections:
                override = input("Sections JSON already populated, override? (y/n): ")

                if override.lower() != "y":
                    return existing_sections

    return None


def save_sections(sections: list[Section], path: Path):
    """Saves the given sections to the given path"""
    with open(path, "w") as file:
        _ = file.write(
            json.dumps(
                [
                    section.model_dump(mode="json", by_alias=True)
                    for section in sections
                ],
                indent=2,
                ensure_ascii=False,
            )
        )


def get_semester(lines: list[list[Word]]):
    """
    Gets the semester of the pdf from the given lines
    """

    title = get_line_text(lines[0])
    return title.replace("SCHEDULE OF CLASSES - ", "")


def parse_and_save(
    sorted_lines: list[list[Word]],
    columns_x: ColumnsXs,
    parsed_sections_path: Path,
    override: bool | None,
) -> list[Section]:
    """
    Parse given the sorted liines and return the parsed sections if override is true.
    """

    if s := contains_data(
        override, parsed_sections_path, "Parsed sections already populated."
    ):
        return TypeAdapter(list[Section]).validate_json(s)

    parser = NewParser()
    sections = parser.parse(sorted_lines, columns_x)

    with open(parsed_sections_path, "w") as f:
        dumpable_sections = [section.model_dump(by_alias=True) for section in sections]
        json.dump(dumpable_sections, f, indent=2, ensure_ascii=False)

    return sections


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    files = Files()
    parser = NewParser()

    sorted_lines_dict = compute_sorted_lines(files.pdf_path)
    columns_x = compute_columns_x(sorted_lines_dict)
    _ = parse_and_save(
        list(sorted_lines_dict.values()), columns_x, files.parsed_sections_path, None
    )

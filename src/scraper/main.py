import datetime
from logging import log
import logging
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv

from scraper.parser_utils import (
    compute_columns_x_if_not_exists,
    compute_sorted_lines_if_not_exist,
)
from scraper.util import (
    get_global_sections_diff,
    make_global_sections_final,
    make_sections_final,
)

from scraper.new_parser import NewParser, get_semester, parse_and_save
from scraper.files import Files
from scraper.scraper import Scraper
import pytest
import typer


def get_current_semester() -> str:
    """
    Gets the current semester at the time this function got called
    """

    now = datetime.datetime.now()

    if 6 <= now.month < 12:
        return f"FALL {now.year}"
    elif now.month == 12:
        return f"WINTER {now.year + 1}"
    elif 1 <= now.month < 6:
        return f"WINTER {now.year}"
    else:
        return f"SUMMER {now.year}"


def the_entire_loop(files: Files):
    semester = get_current_semester()

    print(f"parsing pdf at {files.pdf_path}")

    parser = NewParser(files)
    scraper = Scraper(files)

    sections = parser.run(True)
    ratings = scraper.run(True)
    section_by_id = make_sections_final(sections, ratings, files)

    parsed_semester = parser.get_semester()

    if parsed_semester != semester:
        log(
            logging.WARN,
            f"Parsed and current semester differs: parsed {parsed_semester}, current {semester}",
        )

    schedule_diff = get_global_sections_diff(
        semester, files.get_global_all_sections_content(), section_by_id
    )
    _ = make_global_sections_final(semester, section_by_id, files, schedule_diff, [])


def _main(
    pdf_path: Annotated[str, typer.Option(help="Path to the schedule of classes file")],
    override: Annotated[
        bool | None,
        typer.Option(
            help="Override everything [true] or always used saved data [false]. Omitting this will ask the user for confirmation when there is saved data."
        ),
    ] = None,
    run_tests: Annotated[bool, typer.Option(help="Run tests")] = False,
):
    """
    Parse the schedule of classes pdf and scrape professors' ratings into an ultimate compilation of all sections
    """
    _ = load_dotenv()

    files = Files(pdf_path=Path(pdf_path))
    semester = get_current_semester()

    print(f"parsing pdf at {files.pdf_path}")

    sorted_lines_dict = compute_sorted_lines_if_not_exist(
        files.sorted_lines_path, files.pdf_path, override
    )
    columns_x = compute_columns_x_if_not_exists(
        files.section_columns_x_path, sorted_lines_dict, override
    )
    sorted_lines = list(sorted_lines_dict.values())

    sections = parse_and_save(
        sorted_lines, columns_x, files.parsed_sections_path, override
    )

    scraper = Scraper(files)

    ratings = scraper.run(yes)
    section_by_id = make_sections_final(sections, ratings, files)

    parsed_semester = get_semester(sorted_lines)

    if parsed_semester != semester:
        log(
            logging.WARN,
            f"Parsed and current semester differs: parsed {parsed_semester}, current {semester}",
        )

    schedule_diff = get_global_sections_diff(
        semester, files.get_global_all_sections_content(), section_by_id
    )
    _ = make_global_sections_final(semester, section_by_id, files, schedule_diff, [])

    if run_tests:
        exit(pytest.main(["--no-header", "-s", "-v"]))


def main():
    typer.run(_main)


if __name__ == "__main__":
    main()

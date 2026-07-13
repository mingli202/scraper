import datetime
from logging import log
import logging
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv

from scraper import util
from scraper.models import GlobalAllSections
from scraper.parser_utils import (
    get_parser_deps,
    get_parser_deps_if_not_exists,
)
from scraper.util import (
    add_rating_to_sections,
    get_global_sections_diff,
    save_global_sections_final,
    make_sections_final,
    should_override,
)

from scraper.new_parser import NewParser, get_semester, parse_and_save
from scraper.files import Files
from scraper.scraper import scrape, scrape_with_override
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


def the_entire_loop(pdf_path: Path, pids_path: Path) -> GlobalAllSections:
    """The entire loop with no cache and no diff"""

    semester = get_current_semester()

    log(logging.DEBUG, f"parsing pdf at {pdf_path}")

    parser = NewParser()
    sorted_lines, columns_x = get_parser_deps(pdf_path)
    sections = parser.parse(sorted_lines, columns_x)

    professors = util.get_professors_from_sections(sections)
    pids = util.get_saved_pids(pids_path)

    ratings = scrape(professors, pids, False)
    add_rating_to_sections(sections, ratings)
    sections_by_id = util.to_sections_by_id(sections)

    parsed_semester = get_semester(sorted_lines)

    if parsed_semester != semester:
        log(
            logging.WARN,
            f"Parsed and current semester differs: parsed {parsed_semester}, current {semester}",
        )

    return GlobalAllSections(
        semester=semester,
        sections_by_id=sections_by_id,
        filename=pdf_path.name,
        sections_diff=None,
        comments=[],
    )


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

    sorted_lines, columns_x = get_parser_deps_if_not_exists(
        files.sorted_lines_path, files.pdf_path, files.columns_x_path, override
    )

    sections = parse_and_save(
        sorted_lines, columns_x, files.parsed_sections_path, override
    )

    ratings = scrape_with_override(
        sections, files.ratings_path, files.pids_path, override, False
    )
    make_sections_final(sections, ratings, files.all_sections_final_path_json)
    sections_by_id = util.to_sections_by_id(sections)

    parsed_semester = get_semester(sorted_lines)

    if parsed_semester != semester:
        log(
            logging.WARN,
            f"Parsed and current semester differs: parsed {parsed_semester}, current {semester}",
        )

    schedule_diff = get_global_sections_diff(
        semester, files.get_global_all_sections_content(), sections_by_id
    )

    if should_override(
        override,
        files.global_all_sections_final_path_json,
        "Global all sections already exists.",
    ):
        _ = save_global_sections_final(
            semester,
            sections_by_id,
            files.pdf_path,
            files.global_all_sections_final_path_json,
            schedule_diff,
            [],
        )

    if run_tests:
        exit(pytest.main(["--no-header", "-s", "-v"]))


def main():
    typer.run(_main)


if __name__ == "__main__":
    main()

import datetime
from logging import log
import logging
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv

from scraper.util import (
    get_schedule_diff,
    make_global_sections_final,
    make_sections_final,
)

from .new_parser import NewParser
from .files import Files
from .scraper import Scraper
import pytest
import typer


def get_current_semester() -> str:
    """
    Gets the current semester at the time this function got called
    """

    now = datetime.datetime.now()

    if 8 <= now.month < 12:
        return f"FALL {now.year}"
    elif now.month == 12:
        return f"WINTER {now.year + 1}"
    elif 1 <= now.month < 7:
        return f"WINTER {now.year}"
    else:
        return f"SUMMER {now.year}"


def _main(
    pdf_path: Annotated[str, typer.Option(help="Path to the schedule of classes file")],
    yes: Annotated[
        bool, typer.Option(help="Answer yes to all override prompts")
    ] = False,
    run_tests: Annotated[bool, typer.Option(help="Run tests")] = False,
):
    """
    Parse the schedule of classes pdf and scrape professors' ratings into an ultimate compilation of all sections
    """
    _ = load_dotenv()

    files = Files(pdf_path=Path(pdf_path))
    semester = get_current_semester()

    print(f"parsing pdf at {files.pdf_path}")

    parser = NewParser(files)
    scraper = Scraper(files)

    sections = parser.run(yes)
    ratings = scraper.run(yes)
    section_by_id = make_sections_final(sections, ratings, files)

    parsed_semester = parser.get_semester()

    if parsed_semester != semester:
        log(
            logging.WARN,
            f"Parsed and current semester differs: parsed {parsed_semester}, current {semester}",
        )

    schedule_diff = get_schedule_diff(semester, section_by_id, files)
    make_global_sections_final(semester, section_by_id, files, schedule_diff)

    if run_tests:
        exit(pytest.main(["--no-header", "-s", "-v"]))


def main():
    typer.run(_main)


if __name__ == "__main__":
    main()

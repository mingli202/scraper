import logging
import sys
from pathlib import Path
from typing import Annotated

import pytest
import typer
from dotenv import load_dotenv

from scraper import lib, util
from scraper.files import Files
from scraper.new_parser import get_semester, parse_and_save
from scraper.parser_utils import (
    get_parser_deps_if_not_exists,
)
from scraper.scraper import scrape_with_override
from scraper.util import (
    contains_data,
    get_global_sections_diff,
    make_sections_final,
    save_global_sections_final,
)

logger = logging.getLogger(__name__)


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
    semester = lib.get_current_semester()

    logger.info(f"parsing pdf at {files.pdf_path}")

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
        logger.warning(
            f"Parsed and current semester differs: parsed {parsed_semester}, current {semester}",
        )

    schedule_diff = get_global_sections_diff(
        semester, files.get_global_all_sections_content(), sections_by_id
    )

    if not contains_data(
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
        sys.exit(pytest.main(["--no-header", "-s", "-v"]))


def main():
    typer.run(_main)


if __name__ == "__main__":
    main()

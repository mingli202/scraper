from typing import Annotated
from .new_parser import NewParser
from . import util
from .files import Files
from .scraper import Scraper
import pytest
import typer


# TODO: 1. Change filename and semester in files.py
def main(
    yes: Annotated[
        bool, typer.Option(help="Answer yes to all override prompts")
    ] = False,
    run_tests: Annotated[bool, typer.Option(help="Run tests")] = False,
):
    """
    Parse the schedule of classes pdf and scrape professor's ratings into an ultimate compilation of all sections
    """

    files = Files()
    parser = NewParser(files)
    scraper = Scraper(files)

    parser.run(yes)
    scraper.run(yes)

    util.save_sections_with_viewData(files, yes)

    if run_tests:
        exit(pytest.main(["--no-header", "-s", "-v"]))


if __name__ == "__main__":
    typer.run(main)

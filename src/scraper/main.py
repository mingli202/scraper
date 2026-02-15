from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from .new_parser import NewParser
from . import db
from .files import Files
from .scraper import Scraper
import pytest
import typer


# TODO: 1. Change filename and semester in files.py
def _main(
    yes: Annotated[
        bool, typer.Option(help="Answer yes to all override prompts")
    ] = False,
    run_tests: Annotated[bool, typer.Option(help="Run tests")] = False,
):
    """
    Parse the schedule of classes pdf and scrape professors' ratings into an ultimate compilation of all sections
    """
    db.init_db()
    _ = load_dotenv()

    files = Files(
        Path(
            "/Users/vincentliu/Downloads/SCHEDULE_OF_CLASSES_Winter_2026_December_11.pdf"
        )
    )

    parser = NewParser(files)
    scraper = Scraper(files)

    parser.run(yes)
    scraper.run(yes)

    if run_tests:
        exit(pytest.main(["--no-header", "-s", "-v"]))


def main():
    typer.run(_main)


if __name__ == "__main__":
    main()

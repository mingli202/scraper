from new_parser import NewParser
import util
from files import Files
from scraper import Scraper
import pytest


# TODO: 1. Change filename and semester in files.py
def main():
    files = Files()
    parser = NewParser(files)
    scraper = Scraper(files)

    parser.run()
    scraper.run()

    util.save_sections_with_viewData(files)


if __name__ == "__main__":
    main()
    exit(pytest.main(["--no-header", "-s", "-v"]))

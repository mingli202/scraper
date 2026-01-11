from new_parser import NewParser
import util
from files import Files
from scraper import Scraper
import pytest


# TODO: 1. Change filename and semester in files.py
def main():
    files = Files()
    parser = NewParser(files)
    ratings = Scraper(files)

    parser.run()
    ratings.run()

    util.addRating(files)
    util.addViewData(files)


if __name__ == "__main__":
    main()
    exit(pytest.main(["--no-header", "-s", "-v"]))

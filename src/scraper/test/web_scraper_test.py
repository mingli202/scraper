from pathlib import Path
from pydantic import TypeAdapter
import pytest

from scraper import util
from scraper.files import Files
import scraper.scraper as scraper

from scraper.models import Rating, Section, Status


pdf_path = (
    Path(__file__).parent.parent.parent.parent
    / "RPHOR200_-_Schedule_of_classes_F26_JUNE_12"
)

files = Files(pdf_path)
pids = util.get_saved_pids(files.pids_path)
professors: list[str] = []
with open(files.parsed_sections_path, "r") as file:
    s = file.read()
    parsed_sections = TypeAdapter(list[Section]).validate_json(s)
    professors = util.get_professors_from_sections(parsed_sections)


def test_prof_rating_regex():
    assert scraper.get_stats_from_pid("817818", "Grant, Grell") is not None


def test_unique_lastname():
    not_unique_last_name: set[str] = set()

    lastnames: set[str] = set()
    for prof in professors:
        lname, _ = prof.split(", ")
        if lname != "TBA-1" and lname in lastnames:
            not_unique_last_name.add(prof)

        else:
            lastnames.add(lname)

    if not_unique_last_name.__len__() > 0:
        print(not_unique_last_name)


def test_closelness():
    c = scraper.closeness("Grgoy", "Gregory")
    assert c == 5 / 7

    c = scraper.closeness("Greg", "Gregory")
    assert c == 4 / 7


def test_valid_pids():
    pids = scraper.get_pids("wang")
    assert len(pids) == 1


def test_duplicate_pids():
    pids = scraper.get_pids("Provencher")
    assert len(pids) == 2  # there are 2 provencher


def test_no_pids():
    pids = scraper.get_pids("Klochko")
    assert len(pids) == 0  # results are N/A


def test_department_with_space_and_duplicate_pids():
    pids = scraper.get_pids("young")
    assert len(pids) == 2  # department had a space


def test_missing_rating():
    rating = scraper.get_rating("Voinea, Sorin", pids)
    assert rating == Rating(prof="Voinea, Sorin")


# NOTE: these are hardcoded values, so subject to change
def test_valid_rating():
    rating = scraper.get_rating("Trepanier, Michele", pids)
    assert rating == Rating(
        prof="Trepanier, Michele",
        avg=3.0,
        takeAgain=48,
        difficulty=3.5,
        nRating=23,
        status=Status.FOUND,
        score=59.2,
        pId="2496979",
    )


def test_duplicate_rating():
    rating: Rating = scraper.get_rating("Young, Ryan", pids)
    assert rating == Rating(
        prof="Young, Ryan",
        avg=2.5,
        takeAgain=36,
        difficulty=2.6,
        nRating=10,
        status=Status.FOUND,
        score=50.0,
        pId="2713391",
    )

    rating = scraper.get_rating("Young, Thomas", pids)

    assert rating == Rating(
        prof="Young, Thomas",
        score=68.3,
        avg=3.5,
        takeAgain=55,
        difficulty=2.4,
        nRating=21,
        status=Status.FOUND,
        pId="1974605",
    )


# NOTE: belongs to Concordia
def test_Klochko_Yuliya():
    if "Klochko, Yuliya" not in professors:
        return

    rating: Rating = scraper.get_rating("Klochko, Yuliya", pids)
    assert rating == Rating(prof="Klochko, Yuliya")


def test_special_cases():
    rating: Rating = scraper.get_rating("Lo Vasco, Frank", pids)
    assert rating == Rating(
        prof="Lo Vasco, Frank",
        avg=3.1,
        takeAgain=48,
        difficulty=4.2,
        nRating=61,
        status=Status.FOUND,
        score=61.6,
        pId="898891",
    )


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-vvv", __file__]))

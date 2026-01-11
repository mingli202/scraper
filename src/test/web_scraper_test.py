import os
import pytest

from pydantic_core import from_json
from files import Files

from models import Rating
from scraper import Scraper
import json


files = Files()
professors: list[str] = []
with open(files.professors_path, "r") as file:
    professors = from_json(file.read())
scraper = Scraper(files)


def test_prof_rating_regex():
    assert scraper.get_stats_from_pid("817818", "Grant, Grell") is not None


def test_unique_lastname():
    professors: list[str] = files.get_professors_file_content().get_words("")

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
    rating, _ = scraper.get_rating("Voinea, Sorin", scraper.get_saved_pids())
    assert rating == Rating(prof="Voinea, Sorin")


# NOTE: these are hardcoded values, so subject to change
def test_valid_rating():
    rating = scraper.get_rating("Trepanier, Michele", scraper.get_saved_pids())[0]
    assert rating == Rating(
        prof="Trepanier, Michele",
        avg=3.0,
        takeAgain=50,
        difficulty=3.5,
        nRating=22,
        status="found",
        score=59.2,
    )


def test_duplicate_rating():
    rating: Rating = scraper.get_rating("Young, Ryan", scraper.get_saved_pids())[0]
    assert rating == Rating(
        prof="Young, Ryan",
        avg=2.2,
        takeAgain=22,
        difficulty=2.8,
        nRating=9,
        status="found",
        score=45.1,
    )

    rating = scraper.get_rating("Young, Thomas", scraper.get_saved_pids())[0]

    assert rating == Rating(
        prof="Young, Thomas",
        score=68.2,
        avg=3.5,
        takeAgain=53,
        difficulty=2.5,
        nRating=20,
        status="found",
    )


# NOTE: belongs to Concordia
def test_Klochko_Yuliya():
    if "Klochko, Yuliya" not in professors:
        return

    rating: Rating = scraper.get_rating("Klochko, Yuliya", scraper.get_saved_pids())[0]
    assert rating == Rating(prof="Klochko, Yuliya")


# NOTE: manually check foundn't
# NOTE: winter2026 dec 11 schedule pdf checked!
# NOTE: missingPids checked!
def test_accuracy_of_not_found():
    checked = True
    updated = True

    if checked:
        if not updated:
            update_section_with_checked_pids()
        return

    odd: dict[str, str] = {}

    ratings: dict[str, Rating] = files.get_ratings_file_content()

    if os.path.exists(files.missing_pids_path):
        with open(files.missing_pids_path, "r") as file:
            odd = json.loads(file.read())

    for rating in ratings.values():
        if rating.status == "foundn't":
            odd[rating.prof] = ""

    if len(odd) > 0:
        print(json.dumps(odd, indent=2))

    with open(files.missing_pids_path, "w") as file:
        _ = file.write(json.dumps(odd, indent=2))

    assert len(odd) == 0


def update_section_with_checked_pids():
    ratings = files.get_ratings_file_content()
    pids = {k: v for k, v in files.get_missing_pids_file_content().items() if v != ""}
    new_pids = files.get_pids_file_content()
    scraper.scrape_ratings(list(pids.keys()), ratings, pids, new_pids)

    assert ratings["Walker, Tara Leigh"].status == "found"

    with open(files.ratings_path, "w") as file:
        _ = file.write(
            json.dumps({k: v.model_dump() for k, v in ratings.items()}, indent=2)
        )

    with open(files.pids_path, "w") as file:
        _ = file.write(json.dumps(new_pids, indent=2))


def test_special_cases():
    rating: Rating = scraper.get_rating("Lo Vasco, Frank", scraper.get_saved_pids())[0]
    assert rating == Rating(
        prof="Lo Vasco, Frank",
        avg=3.2,
        takeAgain=49,
        difficulty=4.1,
        nRating=55,
        status="found",
        score=63.5,
    )


def test_prof_trie():
    professors = files.get_professors_file_content().get_words("")
    old_professors: list[str] = []

    with open(files.cwd / "winter" / "winter-professors.json", "r") as file:
        old_professors = from_json(file.read())

    professors = sorted(professors)
    old_professors = sorted(old_professors)
    assert len(professors) == len(old_professors)
    assert professors == old_professors


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-vvv", __file__]))

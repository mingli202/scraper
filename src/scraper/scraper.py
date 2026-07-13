import json
import re
from collections import OrderedDict
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from pydantic import TypeAdapter

from scraper import util
from scraper.files import Files
from scraper.models import Rating, Section, Status


def scrape_with_override(
    parsed_sections: list[Section],
    ratings_path: Path,
    pids_path: Path,
    override: bool | None,
    debug: bool,
) -> dict[str, Rating]:
    """
    Gets the rating for all professors in the given parsed_sections.

    SIDE EFFECT: will write to pids and ratings file if override
    """

    if s := util.should_override(
        override, ratings_path, "Ratings JSON already populated."
    ):
        return TypeAdapter(dict[str, Rating]).validate_json(s)

    professors = util.get_professors_from_sections(parsed_sections)
    pids = util.get_saved_pids(pids_path)

    ratings = scrape(professors, pids, debug)
    _save_pids(ratings.values(), pids_path)

    _save_ratings(ratings_path, ratings)

    return ratings


def scrape(
    professors: list[str],
    saved_pids: dict[str, str | None],
    debug: bool,
) -> dict[str, Rating]:
    """
    Returns the dict of ratings for all the given professors,
    where the key if the prof and the value if the rating if any
    """

    print("SCRAPING RATINGS")

    def fn(prof: str) -> tuple[Rating, str]:
        rating = _get_rating(prof, saved_pids)
        print(rating)
        return rating, prof

    if debug:
        results = [fn(p) for p in professors]
    else:
        with ThreadPoolExecutor() as e:
            results = e.map(fn, professors)

    ratings: dict[str, Rating] = {}

    for rating, prof in results:
        ratings[prof] = rating

    print("FINISHED SCRAPING")

    return ratings


def _save_pids(ratings: Iterable[Rating], pids_path: Path):
    """
    Saves the pids of all the profs of the given ratings
    as prof: id sorted dict by prof
    """
    pids_map = {rating.prof: rating.pId for rating in ratings}
    sorted_map = OrderedDict(sorted(pids_map.items()))

    with open(pids_path, "w") as file:
        json.dump(sorted_map, file)


def _get_rating(prof: str, saved_pids: dict[str, str | None]) -> Rating:
    """
    Get the rating for the given prof with the given saved_pids dict.
    If the pid is not saved, then try to get the pid of the given prof
    """

    print("GETTING RATING")
    id = _get_prof_id_from_saved_pids(prof, saved_pids)

    if id is None:
        return Rating(prof=prof)

    if rating := _get_stats_from_pid(id, prof):
        return rating
    else:
        return Rating(prof=prof, pId=id)


def _get_prof_id_from_saved_pids(
    prof: str, saved_pids: dict[str, str | None]
) -> str | None:
    """
    Gets the id from the saved pids, otherwise try to get it from rate my professor
    """

    has_pid = (
        prof in saved_pids
        and saved_pids.get(prof) is not None
        and saved_pids[prof] != ""
    )

    if has_pid:
        return saved_pids[prof]
    else:
        return _get_pid_of_closest_prof(prof)


def _get_pid_of_closest_prof(prof: str) -> str | None:
    _prof = util.normalize_string(prof).lower()

    fname = _prof.split(", ")[1]
    lname = _prof.split(", ")[0]

    pids = _get_pids(lname)
    if len(pids) == 0:
        return None

    max = 0
    id = pids[0][0]
    if len(pids) > 1:
        for pid in pids:
            c = _closeness(pid[1].lower(), fname)
            if c > max and c > 0.5:
                id = pid[0]
                max = c

    return id


def _get_pids(lastname: str) -> list[tuple[str, str]]:
    SCHOOL_REF = "U2Nob29sLTEyMDUw"

    url = f"https://www.ratemyprofessors.com/search/professors/12050?q={lastname}"
    r = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:139.0) Gecko/20100101 Firefox/139.0"
        },
    )

    if r.status_code != 200:
        raise

    return re.findall(
        r'{"__id":"[\w=]+","__typename":"Teacher","id":"[\w=]+","legacyId":(\d+),"avgRating":[\d\.]+,"numRatings":[\d\.]+,"wouldTakeAgainPercent":[\d\.]+,"avgDifficulty":[\d\.]+,"department":"[\w ]+","school":{"__ref":"'
        + f"{SCHOOL_REF}"
        + r'"},"firstName":"([\w\' \-,]+)","lastName":'
        + f'"{lastname}'
        + r',?","isSaved":false}',
        r.text,
        re.I,
    )


def _save_ratings(ratings_path: Path, ratings: dict[str, Rating]):
    """
    Saves the ratings at the given ratings_path
    """

    print("SAVING RATINGS")
    print(ratings)

    dumpable = sorted(
        (
            (prof, rating.model_dump(mode="json", by_alias=True))
            for [prof, rating] in ratings.items()
        ),
        key=lambda x: x[0],
    )

    with open(ratings_path, "w") as file:
        json.dump(OrderedDict(dumpable), file)


def _get_stats_from_pid(pid: str, prof: str) -> Rating | None:
    SCHOOL_ID = 12050
    SCHOOL_REF = "U2Nob29sLTEyMDUw"

    url = f"https://www.ratemyprofessors.com/ShowRatings.jsp?tid={pid}"
    r = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:139.0) Gecko/20100101 Firefox/139.0"
        },
    )

    if r.status_code != 200:
        print("Error")
        raise

    if matches := re.search(
        rf'"__typename":"Teacher".+"legacyId":{pid}'
        + r',"firstName":"[\w\' \-,]+","lastName":"[\w\' \-,]+","department":"[\w ,]+","school":{"__ref":"'
        + f"{SCHOOL_REF}"
        + r'"}.+"numRatings":([\d\.]+).+"avgRating":([\d\.]+).+"avgDifficulty":([\d\.]+),"wouldTakeAgainPercent":([\d\.]+).+'
        + rf'"__typename":"School","legacyId":{SCHOOL_ID}',
        r.text,
    ):
        (
            numRating,
            avgRating,
            difficulty,
            takeAgain,
        ) = matches.groups()

        try:
            rating = Rating(
                pId=pid,
                prof=prof,
                nRating=round(float(numRating)),
                avg=round(float(avgRating), 1),
                takeAgain=round(float((takeAgain))),
                difficulty=round(float(difficulty), 1),
                status=Status.FOUND,
            )

            rating.score = round(
                (((rating.avg * rating.nRating) + 5) / (rating.nRating + 2)) * 100 / 5,
                1,
            )

            return rating
        except ValueError:
            return None

    return None


def _closeness(candidate: str, target: str) -> float:
    i = 0
    for char in target:
        if char == candidate[i]:
            i += 1
            if i == len(candidate):
                break

    return i / len(target)


if __name__ == "__main__":
    files = Files()
    parsed_sections = files.get_parsed_sections_file_content()
    _ = scrape_with_override(
        parsed_sections, files.ratings_path, files.pids_path, True, False
    )

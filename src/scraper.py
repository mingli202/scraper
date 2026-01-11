import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
import unittest

import requests
from files import Files
from models import Rating, Section
from pydantic_core import from_json

import util


class Scraper:
    def __init__(self, files: Files):
        self.files = files
        self.debug = False

    def run(self):
        if os.path.exists(self.files.ratings_path):
            with open(self.files.ratings_path, "r") as file:
                ratings = json.loads(file.read())

            if ratings.__len__() != 0:
                print("Rating files already exists")

                if not unittest.main(
                    exit=False, module="test.web_scraper_test"
                ).result.wasSuccessful():
                    print("scraper test unsuccessful")
                    exit(1)

                return

        professors = self.get_professors()

        ratings: dict[str, Rating] = {}
        pids = self.get_saved_pids()

        new_pids: dict[str, str] = {}

        self.scrape_ratings(professors, ratings, pids, new_pids)

        with open(self.files.ratings_path, "w") as file:
            _ = file.write(
                json.dumps({k: v.model_dump() for k, v in ratings.items()}, indent=2)
            )

        with open(self.files.pids_path, "w") as file:
            _ = file.write(json.dumps(new_pids, indent=2))

        if not unittest.main(
            exit=False, module="test.web_scraper_test"
        ).result.wasSuccessful():
            print("scraper test unsuccessful")
            exit(1)

    def scrape_ratings(
        self,
        professors: list[str],
        ratings: dict[str, Rating],
        pids: dict[str, str],
        new_pids: dict[str, str],
    ):
        def fn(prof: str) -> tuple[Rating, str, str]:
            rating, pid = self.get_rating(prof, pids)
            print(rating)
            return rating, prof, pid

        if self.debug:
            results = [fn(p) for p in professors]
        else:
            with ThreadPoolExecutor() as e:
                results = e.map(fn, professors)

        for rating, prof, pid in results:
            ratings[prof] = rating
            new_pids[prof] = pid

    def get_saved_pids(self) -> dict[str, str]:
        if not os.path.exists(self.files.pids_path):
            with open(self.files.pids_path, "w") as file:
                _ = file.write(json.dumps({}))

        with open(self.files.pids_path, "r") as file:
            return from_json(file.read())

    def get_professors(self) -> list[str]:
        if not os.path.exists(self.files.professors_path):
            profs: set[str] = set()
            with open(self.files.parsed_sections, "r") as file:
                classes: list[Section] = [Section(**d) for d in from_json(file.read())]

                for cl in classes:
                    for time in cl.times:
                        if time.prof != "":
                            profs.add(time.prof)

            profs.remove("")

            with open(self.files.professors_path, "w") as file:
                _ = file.write(json.dumps(list(profs), indent=2))

        professors: list[str] = []
        with open(self.files.professors_path, "r") as file:
            professors = from_json(file.read())

        return professors

    def get_rating(self, prof: str, saved_pids: dict[str, str]) -> tuple[Rating, str]:
        rating = Rating(prof=prof)

        if prof in saved_pids and saved_pids[prof] != "":
            id = saved_pids[prof]
        else:
            _prof = util.stripAccent(prof).lower()

            fname = _prof.split(", ")[1]
            lname = _prof.split(", ")[0]

            pids = self.get_pids(lname)
            if len(pids) == 0:
                return rating, ""

            max = 0
            id = pids[0][0]
            if len(pids) > 1:
                for pid in pids:
                    c = self.closeness(pid[1].lower(), fname)
                    if c > max and c > 0.5:
                        id = pid[0]
                        max = c

        if _r := self.get_stats_from_pid(id, prof):
            rating = _r

        return rating, id

    def closeness(self, candidate: str, target: str) -> float:
        i = 0
        for char in target:
            if char == candidate[i]:
                i += 1
                if i == len(candidate):
                    break

        return i / len(target)

    def get_pids(self, lastname: str) -> list[tuple[str, str]]:
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

    def get_stats_from_pid(self, pid: str, prof: str) -> Rating | None:
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
                    prof=prof,
                    nRating=round(float(numRating)),
                    avg=round(float(avgRating), 1),
                    takeAgain=round(float((takeAgain))),
                    difficulty=round(float(difficulty), 1),
                    status="found",
                )

                rating.score = round(
                    (((rating.avg * rating.nRating) + 5) / (rating.nRating + 2))
                    * 100
                    / 5,
                    1,
                )

                return rating
            except ValueError:
                return None

        return None

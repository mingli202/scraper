import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
import sqlite3

from pydantic import TypeAdapter
import requests
from files import Files
from models import Rating

import util


class Scraper:
    def __init__(self, files: Files):
        self.files = files
        self.debug = False

    def run(self):
        if self.files.all_sections_final_path.exists():
            conn = sqlite3.connect(self.files.all_sections_final_path)
            cursor = conn.cursor()
            res = cursor.execute(
                "SELECT name from sqlite_schema WHERE type='table' and tbl_name='ratings'"
            )
            if res.fetchone() is not None:
                print("Rating files already exists")

                override = input("Rating files already exists, override? (y/n)")
                if override.lower() != "y":
                    return

        professors = self.files.get_professors_file_content().get_words("")

        ratings: dict[str, Rating] = {}
        pids = self.get_saved_pids()

        new_pids: dict[str, str | None] = {}

        self.scrape_ratings(professors, ratings, pids, new_pids)

        with open(self.files.pids_path, "w") as file:
            _ = file.write(json.dumps(new_pids, indent=2))

        self.save_ratings(ratings)

    def scrape_ratings(
        self,
        professors: list[str],
        ratings: dict[str, Rating],
        pids: dict[str, str | None],
        new_pids: dict[str, str | None],
    ):
        def fn(prof: str) -> tuple[Rating, str]:
            rating = self.get_rating(prof, pids)
            print(rating)
            return rating, prof

        if self.debug:
            results = [fn(p) for p in professors]
        else:
            with ThreadPoolExecutor() as e:
                results = e.map(fn, professors)

        for rating, prof in results:
            ratings[prof] = rating
            new_pids[prof] = rating.pId

    def get_saved_pids(self) -> dict[str, str | None]:
        if not os.path.exists(self.files.pids_path):
            with open(self.files.pids_path, "w") as file:
                _ = file.write(json.dumps({}))

        with open(self.files.pids_path, "r") as file:
            adapter = TypeAdapter(dict[str, str | None])
            return adapter.validate_json(file.read())

    def get_rating(self, prof: str, saved_pids: dict[str, str | None]) -> Rating:
        rating = Rating(prof=prof)

        if (
            prof in saved_pids
            and saved_pids.get(prof) is not None
            and saved_pids[prof] != ""
        ):
            id = saved_pids[prof]
        else:
            _prof = util.normalize_string(prof).lower()

            fname = _prof.split(", ")[1]
            lname = _prof.split(", ")[0]

            pids = self.get_pids(lname)
            if len(pids) == 0:
                return rating

            max = 0
            id = pids[0][0]
            if len(pids) > 1:
                for pid in pids:
                    c = self.closeness(pid[1].lower(), fname)
                    if c > max and c > 0.5:
                        id = pid[0]
                        max = c

        assert id is not None
        if _r := self.get_stats_from_pid(id, prof):
            rating = _r

        rating.pId = id

        return rating

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

    def save_ratings(self, ratings: dict[str, Rating]):
        conn = sqlite3.connect(self.files.all_sections_final_path)
        cursor = conn.cursor()

        _ = cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                prof TEXT PRIMARY KEY NOT NULL,
                score REAL NOT NULL,
                avg REAL NOT NULL,
                nRating INTEGER NOT NULL,
                takeAgain INTEGER NOT NULL,
                difficulty REAL NOT NULL,
                status TEXT NOT NULL,
                pId TEXT
            )
        """)

        rows = [
            (
                rating.prof,
                rating.score,
                rating.avg,
                rating.nRating,
                rating.takeAgain,
                rating.difficulty,
                rating.status,
                rating.pId,
            )
            for rating in ratings.values()
        ]

        _ = cursor.executemany(
            """
            INSERT INTO ratings VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(prof) DO UPDATE SET score=excluded.score, avg=excluded.avg, nRating=excluded.nRating, takeAgain=excluded.takeAgain, difficulty=excluded.difficulty, status=excluded.status, pId=excluded.pId
        """,
            rows,
        )

        conn.commit()
        conn.close()


if __name__ == "__main__":
    files = Files()
    scraper = Scraper(files)
    scraper.run()

import sqlite3
from fastapi import FastAPI
from pydantic import ValidationError
from scraper.files import Files
from scraper.models import LecLab, Rating, Section

app = FastAPI()
files = Files()


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.get("/all_sections")
async def get_all_sections() -> list[Section]:
    conn = sqlite3.connect(files.all_sections_final_path)
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT * FROM sections
    """).fetchall()

    sections = [Section.validate_db_response(r) for r in row]

    for section in sections:
        time_rows = cursor.execute(
            """
            SELECT * FROM times WHERE section_id = ?
        """,
            (section.id,),
        ).fetchall()

        section.times = [LecLab.validate_db_response(r) for r in time_rows]

    conn.close()

    return sections


@app.get("/sections/{section_id}")
async def get_section(section_id: int) -> Section | None:
    conn = sqlite3.connect(files.all_sections_final_path)
    cursor = conn.cursor()

    section_row = cursor.execute(
        """
        SELECT * FROM sections WHERE id = ?
    """,
        (section_id,),
    ).fetchone()

    time_rows = cursor.execute(
        """
        SELECT * FROM times WHERE section_id = ?
    """,
        (section_id,),
    ).fetchall()

    conn.close()

    if section_row is None:
        return None

    try:
        section = Section.validate_db_response(section_row)
        section.times = [LecLab.validate_db_response(r) for r in time_rows]
        return section
    except ValidationError:
        return None


@app.get("/sections/")
async def get_sections(
    q: str | None = None,
    course: str | None = None,
    domain: str | None = None,
    code: str | None = None,
    title: str | None = None,
    teacher: str | None = None,
    min_rating: int | None = None,
    max_rating: int | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
    days_off: str | None = None,
    time_start: str | None = None,
    time_end: str | None = None,
    blended: bool = False,
    honours: bool = False,
) -> list[Section]:
    query = "SELECT * from sections WHERE 1=1"
    params: list[str] = []

    if q is not None:
        query += " AND (course LIKE %?% OR title domain %?% or code %?%)"
        params.extend([q, q, q])

    if course is not None:
        query += " AND course LIKE %?%"
        params.append(course)

    if domain is not None:
        query += " AND domain LIKE %?%"
        params.append(domain)

    if code is not None:
        query += " AND code LIKE %?%"
        params.append(code)

    if blended:
        query += " AND more LIKE 'BLENDED%'"

    if honours:
        query += " AND more LIKE 'For Honours%'"

    conn = sqlite3.connect(files.all_sections_final_path)
    cursor = conn.cursor()

    rating_conn = sqlite3.connect(files.ratings_db_path)
    rating_cursor = rating_conn.cursor()

    rows = cursor.execute(query, params).fetchall()

    sections = [Section.validate_db_response(r) for r in rows]
    valid_sections: list[Section] = []

    for section in sections:
        time_rows = cursor.execute(
            """
            SELECT * FROM times WHERE section_id = ?
        """,
            (section.id,),
        ).fetchall()

        times = [LecLab.validate_db_response(r) for r in time_rows]

        valid_time = True

        for time in times:
            if title is not None and title not in time.title:
                valid_time = False
                break

            if teacher is not None and teacher not in time.prof:
                valid_time = False
                break

            rating_row = rating_cursor.execute(
                """
                SELECT * FROM ratings WHERE prof = ?
            """,
                (time.prof,),
            ).fetchone()

            for d, t in time.time.items():
                if days_off is not None and d in days_off:
                    valid_time = False
                    break

                for t in t:
                    start_str, end_str = t.split("-")

                    if time_start is not None and int(time_start) < int(start_str):
                        valid_time = False
                        break
                    if time_end is not None and int(time_end) > int(end_str):
                        valid_time = False
                        break

            if rating_row is None:
                valid_time = False
                break

            try:
                rating = Rating.validate_db_response(rating_row)
            except ValidationError:
                valid_time = False
                break

            if min_rating is not None and rating.avg < min_rating:
                valid_time = False
                break
            if max_rating is not None and rating.avg > max_rating:
                valid_time = False
                break

            if min_score is not None and rating.score < min_score:
                valid_time = False
                break
            if max_score is not None and rating.score > max_score:
                valid_time = False
                break

        if valid_time:
            section.times = times
            valid_sections.append(section)

    conn.close()

    return valid_sections


@app.get("/ratings/{prof}")
async def get_ratings(prof: str) -> Rating | None:
    conn = sqlite3.connect(files.ratings_db_path)
    cursor = conn.cursor()

    row = cursor.execute(
        """
        SELECT * FROM ratings WHERE prof = ?
    """,
        (prof,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    try:
        return Rating.validate_db_response(row)
    except ValidationError:
        return None

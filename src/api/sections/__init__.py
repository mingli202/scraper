import sqlite3
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from scraper.files import Files
from scraper.models import LecLab, Rating, Section

router = APIRouter(prefix="/sections", tags=["Sections"])
files = Files()


@router.get("/")
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
    days_off: Annotated[str | None, Query(pattern="^[MWTRF]{1,5}$")] = None,
    time_start_query: Annotated[str | None, Query(pattern=r"^\d{4}$")] = None,
    time_end_query: Annotated[str | None, Query(pattern=r"^\d{4}$")] = None,
    blended: bool = False,
    honours: bool = False,
) -> list[Section]:
    query = "SELECT * from sections WHERE 1=1"
    params: list[str] = []

    if q is not None:
        query += " AND (title LIKE ? OR course LIKE ? OR domain LIKE ? OR code LIKE ?)"
        params.extend([f"%{q}%", f"{q}%", f"{q}%", f"%{q}%"])

    if title is not None:
        query += " AND title LIKE ?"
        params.append(f"%{title}%")

    if course is not None:
        query += " AND course LIKE ?"
        params.append(f"{course}%")

    if domain is not None:
        query += " AND domain LIKE ?"
        params.append(f"{domain}%")

    if code is not None:
        query += " AND code LIKE ?"
        params.append(f"%{code}%")

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

        leclabs = [LecLab.validate_db_response(r) for r in time_rows]

        valid_time = True

        if teacher is not None:
            valid_time = False
            for leclab in leclabs:
                if teacher.lower() in leclab.prof.lower():
                    valid_time = True
                    break

        if not valid_time:
            continue

        for leclab in leclabs:
            for d, t in leclab.time.items():
                if days_off is not None and any(_d in days_off for _d in d):
                    valid_time = False
                    break

                for t in t:
                    start_str, end_str = t.split("-")

                    if time_start_query is not None and int(start_str) < int(
                        time_start_query
                    ):
                        valid_time = False
                        break
                    if time_end_query is not None and int(end_str) > int(
                        time_end_query
                    ):
                        valid_time = False
                        break

                if not valid_time:
                    break

            if not valid_time:
                break

            rating_row = rating_cursor.execute(
                """
                SELECT * FROM ratings WHERE prof = ?
            """,
                (leclab.prof,),
            ).fetchone()

            if rating_row is None:
                valid_time = False
                break

            try:
                rating = Rating.validate_db_response(rating_row)
            except ValidationError:
                valid_time = False
                break

            if (
                min_rating is not None
                and rating.status == "found"
                and rating.avg < min_rating
            ):
                valid_time = False
                break
            if (
                max_rating is not None
                and rating.status == "found"
                and rating.avg > max_rating
            ):
                valid_time = False
                break

            if (
                min_score is not None
                and rating.status == "found"
                and rating.score < min_score
            ):
                valid_time = False
                break
            if (
                max_score is not None
                and rating.status == "found"
                and rating.score > max_score
            ):
                valid_time = False
                break

        if valid_time:
            section.times = leclabs
            valid_sections.append(section)

    conn.close()
    rating_conn.close()

    return valid_sections


@router.get("/{section_id}")
async def get_section(section_id: int) -> Section:
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
        raise HTTPException(status_code=404, detail="Section not found")

    section = Section.validate_db_response(section_row)
    section.times = [LecLab.validate_db_response(r) for r in time_rows]
    return section

import sqlite3
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query

from api.sections.filter_sections import filter_sections
from scraper.files import Files
from scraper.models import LecLab, Section

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
    return filter_sections(
        q,
        course,
        domain,
        code,
        title,
        teacher,
        min_rating,
        max_rating,
        min_score,
        max_score,
        days_off,
        time_start_query,
        time_end_query,
        blended,
        honours,
    )


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

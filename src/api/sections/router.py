from typing import Annotated
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from api.sections.filter_sections import filter_sections
from scraper.db import SessionDep
from scraper.files import Files
from scraper.models import LecLab, Section

router = APIRouter(prefix="/sections", tags=["Sections"])
files = Files()


@router.get("/")
def get_sections(
    session: SessionDep,
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
        session,
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
def get_section(section_id: int, session: SessionDep) -> Section:
    section = session.get(Section, section_id)

    if section is None:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found")

    return section


@router.post("/")
def get_many(ids: list[int], session: SessionDep) -> list[Section]:
    sections = session.exec(select(Section).where(Section.id in ids)).all()

    return list(sections)

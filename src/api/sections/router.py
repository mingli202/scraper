from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Request
from sqlmodel import Session, col, select

from api.sections.cache import SectionCache
from api.sections.filter_cached_sections import filter_cached_sections
from api.sections.filter_sections import filter_sections
from api.sections.queries import section_by_id_statement, with_section_relationships
from scraper.db import engine
from scraper.models import Section, SectionResponse

router = APIRouter(prefix="/sections", tags=["Sections"])


@router.get("/all")
def get_all(request: Request) -> list[SectionResponse]:
    section_cache = getattr(request.app.state, "section_cache", None)

    if isinstance(section_cache, SectionCache):
        return list(section_cache.all_sections)

    with Session(engine) as session:
        statement = with_section_relationships(select(Section))
        sections = session.exec(statement).all()

    return [SectionResponse.model_validate(section) for section in sections]


@router.get("/")
def get_sections(
    request: Request,
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
    time_start: Annotated[str | None, Query(pattern=r"^\d{4}$")] = None,
    time_end: Annotated[str | None, Query(pattern=r"^\d{4}$")] = None,
    blended: bool = False,
    honours: bool = False,
    limit: Annotated[int | None, Query(ge=1, le=500)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SectionResponse]:
    if (
        q is None
        and course is None
        and domain is None
        and code is None
        and title is None
        and teacher is None
        and min_rating is None
        and max_rating is None
        and min_score is None
        and max_score is None
        and days_off is None
        and time_start is None
        and time_end is None
        and not blended
        and not honours
    ):
        return []

    section_cache = getattr(request.app.state, "section_cache", None)
    if isinstance(section_cache, SectionCache):
        return filter_cached_sections(
            section_cache.all_sections,
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
            time_start,
            time_end,
            blended,
            honours,
            limit,
            offset,
        )

    with Session(engine) as session:
        sections = filter_sections(
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
            time_start,
            time_end,
            blended,
            honours,
            limit,
            offset,
        )

    return [SectionResponse.model_validate(section) for section in sections]


@router.get("/{section_id}")
def get_section(section_id: int, request: Request) -> SectionResponse:
    section_cache = getattr(request.app.state, "section_cache", None)
    if isinstance(section_cache, SectionCache):
        section = section_cache.by_id.get(section_id)
        if section is None:
            raise HTTPException(
                status_code=404, detail=f"Section {section_id} not found"
            )
        return section

    with Session(engine) as session:
        section = session.exec(section_by_id_statement(section_id)).first()

    if section is None:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found")

    return SectionResponse.model_validate(section)


@router.post("/")
def get_many(ids: list[int], request: Request) -> list[SectionResponse]:
    section_cache = getattr(request.app.state, "section_cache", None)

    if isinstance(section_cache, SectionCache):
        sections = [section_cache.by_id.get(id) for id in ids]
        sections = [section for section in sections if section is not None]
        return sections

    with Session(engine) as session:
        statement = with_section_relationships(select(Section)).where(
            col(Section.id).in_(ids)
        )
        sections = session.exec(statement).all()

    return [SectionResponse.model_validate(section) for section in sections]

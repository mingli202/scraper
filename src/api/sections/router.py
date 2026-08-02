import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, UploadFile

from api.sections.cache import SectionCache
from api.sections.filter_cached_sections import filter_cached_sections
from api.sections.helpers import (
    copy_upload_to_tempfile,
    load_sections_from_json,
    lookup_section,
)
from scraper.lib import the_entire_loop
from scraper.models import ParsedPdf, Section

MAX_PDF_PAGES = int(os.environ.get("MAX_PDF_PAGES", str(250)))

router = APIRouter(prefix="/sections", tags=["Sections"])


@router.get("/all")
def get_all(request: Request) -> list[Section]:
    section_cache = getattr(request.app.state, "section_cache", None)

    if isinstance(section_cache, SectionCache):
        return list(section_cache.all_sections)

    return list(load_sections_from_json())


@router.post("/parse-pdf")
def parse_uploaded_pdf(file: UploadFile) -> ParsedPdf:
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

    tmp_pdf_path: Path | None = None

    try:
        tmp_pdf_path = copy_upload_to_tempfile(file)

        return the_entire_loop(tmp_pdf_path, max_pages=MAX_PDF_PAGES)

    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=400, detail=f"Could not parse PDF: {err}"
        ) from err
    finally:
        file.file.close()
        if tmp_pdf_path is not None:
            tmp_pdf_path.unlink(missing_ok=True)


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
) -> list[Section]:
    def _is_blank(value: str | None) -> bool:
        return value is None or value.strip() == ""

    if (
        _is_blank(q)
        and _is_blank(course)
        and _is_blank(domain)
        and _is_blank(code)
        and _is_blank(title)
        and _is_blank(teacher)
        and min_rating is None
        and max_rating is None
        and min_score is None
        and max_score is None
        and _is_blank(days_off)
        and _is_blank(time_start)
        and _is_blank(time_end)
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

    return filter_cached_sections(
        load_sections_from_json(),
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


@router.get("/{section_id}")
def get_section(section_id: str, request: Request) -> Section:
    section_cache = getattr(request.app.state, "section_cache", None)
    if isinstance(section_cache, SectionCache):
        section = lookup_section(section_cache.by_id, section_id)
        if section is None:
            raise HTTPException(
                status_code=404, detail=f"Section {section_id} not found"
            )
        return section

    all_sections = load_sections_from_json()
    by_id = {section.id: section for section in all_sections}
    section = lookup_section(by_id, section_id)

    if section is None:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found")

    return section


@router.post("/")
def get_many(ids: list[str], request: Request) -> list[Section]:
    section_cache = getattr(request.app.state, "section_cache", None)

    if isinstance(section_cache, SectionCache):
        cached_sections: list[Section] = []
        for section_id in ids:
            section = lookup_section(section_cache.by_id, section_id)
            if section is not None:
                cached_sections.append(section)
        return cached_sections

    all_sections = load_sections_from_json()
    by_id = {section.id: section for section in all_sections}
    matched_sections: list[Section] = []
    for section_id in ids:
        section = lookup_section(by_id, section_id)
        if section is not None:
            matched_sections.append(section)
    return matched_sections

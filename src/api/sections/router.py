import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, UploadFile

from api.sections.cache import SectionCache
from api.sections.filter_cached_sections import filter_cached_sections
from scraper.files import Files
from scraper.models import Section
from scraper.new_parser import NewParser

router = APIRouter(prefix="/sections", tags=["Sections"])


def _canonical_section_id(section: Section) -> str:
    return f"{section.code}-{section.section}"


def _load_sections_from_json() -> tuple[Section, ...]:
    files = Files()
    global_sections = files.get_global_all_sections_content()
    return tuple(
        section.model_copy(update={"id": _canonical_section_id(section)})
        for section in global_sections.sections_by_id.values()
    )


def _lookup_section(
    by_id: dict[str, Section],
    section_id: str,
) -> Section | None:
    return by_id.get(section_id)


@router.get("/all")
def get_all(request: Request) -> list[Section]:
    section_cache = getattr(request.app.state, "section_cache", None)

    if isinstance(section_cache, SectionCache):
        return list(section_cache.all_sections)

    return list(_load_sections_from_json())


@router.post("/parse-pdf")
def parse_uploaded_pdf(file: UploadFile) -> list[Section]:
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

    content = file.file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty")

    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    tmp_pdf_path: Path | None = None
    files: Files | None = None

    try:
        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            _ = tmp_file.write(content)
            tmp_pdf_path = Path(tmp_file.name)

        files = Files(pdf_path=tmp_pdf_path)
        parser = NewParser(files)
        parser.parse()

        return parser.sections
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
        if files is not None:
            shutil.rmtree(files.data_dir, ignore_errors=True)


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
        _load_sections_from_json(),
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
        section = _lookup_section(section_cache.by_id, section_id)
        if section is None:
            raise HTTPException(
                status_code=404, detail=f"Section {section_id} not found"
            )
        return section

    all_sections = _load_sections_from_json()
    by_id = {section.id: section for section in all_sections}
    section = _lookup_section(by_id, section_id)

    if section is None:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found")

    return section


@router.post("/")
def get_many(ids: list[str], request: Request) -> list[Section]:
    section_cache = getattr(request.app.state, "section_cache", None)

    if isinstance(section_cache, SectionCache):
        cached_sections: list[Section] = []
        for section_id in ids:
            section = _lookup_section(section_cache.by_id, section_id)
            if section is not None:
                cached_sections.append(section)
        return cached_sections

    all_sections = _load_sections_from_json()
    by_id = {section.id: section for section in all_sections}
    matched_sections: list[Section] = []
    for section_id in ids:
        section = _lookup_section(by_id, section_id)
        if section is not None:
            matched_sections.append(section)
    return matched_sections

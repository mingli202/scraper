import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, UploadFile
from sqlmodel import Session, col, select

from api.sections.cache import SectionCache
from api.sections.filter_cached_sections import filter_cached_sections
from api.sections.queries import section_by_id_statement, with_section_relationships
from scraper.db import engine
from scraper.files import Files
from scraper.models import Section, Section
from scraper.new_parser import NewParser
from scraper.section_response_mapper import sections_to_section_responses

router = APIRouter(prefix="/sections", tags=["Sections"])


def _load_sections_from_json() -> tuple[Section, ...]:
    files = Files()
    sections_from_json = files.read_sections_responses()

    if sections_from_json:
        return tuple(sections_from_json)

    with Session(engine) as session:
        statement = with_section_relationships(select(Section)).order_by(
            col(Section.id)
        )
        sections = session.exec(statement).all()

    return tuple(Section.model_validate(section) for section in sections)


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

        return sections_to_section_responses(parser.sections)
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
def get_section(section_id: int, request: Request) -> Section:
    section_cache = getattr(request.app.state, "section_cache", None)
    if isinstance(section_cache, SectionCache):
        section = section_cache.by_id.get(section_id)
        if section is None:
            raise HTTPException(
                status_code=404, detail=f"Section {section_id} not found"
            )
        return section

    files = Files()
    sections_from_json = files.read_sections_responses()
    if not sections_from_json:
        with Session(engine) as session:
            section = session.exec(section_by_id_statement(section_id)).first()
    else:
        section = next(
            (section for section in sections_from_json if section.id == section_id),
            None,
        )

    if section is None:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found")

    if isinstance(section, Section):
        return Section.model_validate(section)

    return section


@router.post("/")
def get_many(ids: list[int], request: Request) -> list[Section]:
    section_cache = getattr(request.app.state, "section_cache", None)

    if isinstance(section_cache, SectionCache):
        sections = [section_cache.by_id.get(id) for id in ids]
        sections = [section for section in sections if section is not None]
        return sections

    sections_by_id = {section.id: section for section in _load_sections_from_json()}
    return [section for id in ids if (section := sections_by_id.get(id)) is not None]

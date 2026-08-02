import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import HTTPException, UploadFile
from pydantic import TypeAdapter

from scraper.files import Files
from scraper.models import Rating, Section


UPLOAD_CHUNK_SIZE = 1024 * 1024
MAX_PDF_UPLOAD_BYTES = int(
    os.environ.get("MAX_PDF_UPLOAD_BYTES", str(10 * 1024 * 1024))
)


def _canonical_section_id(section: Section) -> str:
    return f"{section.code}-{section.section}"


def load_sections_from_json() -> tuple[Section, ...]:
    files = Files()
    global_sections = files.get_global_all_sections_content()
    return tuple(
        section.model_copy(update={"id": _canonical_section_id(section)})
        for section in global_sections.sections_by_id.values()
    )


def lookup_section(
    by_id: dict[str, Section],
    section_id: str,
) -> Section | None:
    return by_id.get(section_id)


def load_ratings() -> dict[str, Rating]:
    files = Files()
    return TypeAdapter(dict[str, Rating]).validate_json(files.ratings_path.read_text())


def copy_upload_to_tempfile(file: UploadFile) -> Path:
    _ = file.file.seek(0)
    if file.file.read(5) != b"%PDF-":
        raise HTTPException(status_code=400, detail="Invalid PDF file")
    _ = file.file.seek(0)

    bytes_written = 0
    tmp_pdf_path: Path | None = None
    try:
        with NamedTemporaryFile(suffix=".pdf", delete=False, dir="/tmp") as tmp_file:
            tmp_pdf_path = Path(tmp_file.name)
            while chunk := file.file.read(UPLOAD_CHUNK_SIZE):
                bytes_written += len(chunk)
                if bytes_written > MAX_PDF_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Uploaded PDF exceeds the {MAX_PDF_UPLOAD_BYTES}-byte limit",
                    )
                _ = tmp_file.write(chunk)

            if bytes_written == 0:
                raise HTTPException(status_code=400, detail="Uploaded PDF is empty")

        assert tmp_pdf_path is not None
        return tmp_pdf_path
    except Exception:
        if tmp_pdf_path is not None:
            tmp_pdf_path.unlink(missing_ok=True)
        raise

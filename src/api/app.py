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

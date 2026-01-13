import sqlite3
from fastapi import FastAPI, HTTPException
from . import sections
from scraper.files import Files
from scraper.models import Rating

app = FastAPI()
files = Files()

app.include_router(sections.router)


@app.get("/")
async def root():
    return {"message": "Hello World!"}


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
        raise HTTPException(status_code=404, detail=f"Rating for {prof} not found")

    return Rating.validate_db_response(row)

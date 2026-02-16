from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlmodel import select
from api.sections.router import router as section_router
from scraper.db import SessionDep, init_db
from scraper.files import Files
from scraper.models import LecLab, Rating


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _ = load_dotenv()
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
files = Files()

app.include_router(section_router)


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ratings/{prof}")
def get_ratings(prof: str, session: SessionDep) -> Rating | None:
    rating = session.get(Rating, prof)

    if rating is None:
        raise HTTPException(status_code=404, detail=f"Rating for {prof} not found")

    return rating


@app.get("/leclab/{section_id}")
def get_leclab(section_id: int, session: SessionDep) -> list[LecLab]:
    return list(session.exec(select(LecLab).where(LecLab.section_id == section_id)))

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select

from api.sections.cache import load_section_cache
from api.sections.router import router as section_router
from scraper.db import SessionDep, init_db
from scraper.models import LecLab, LecLabResponse, Rating, RatingResponse


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _ = load_dotenv()
    init_db()
    _app.state.section_cache = load_section_cache()
    yield


app = FastAPI(lifespan=lifespan)


env = os.environ.get("ENV", "DEV").upper()

origins = (
    [
        "https://dream-builder-hazel.vercel.app/",
    ]
    if env == "PROD"
    else "*"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(section_router)


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ratings/{prof}", response_model=RatingResponse)
def get_ratings(prof: str, session: SessionDep) -> Rating | None:
    rating = session.get(Rating, prof)

    if rating is None:
        raise HTTPException(status_code=404, detail=f"Rating for {prof} not found")

    return rating


@app.get("/leclab/{section_id}", response_model=list[LecLabResponse])
def get_leclab(section_id: int, session: SessionDep) -> list[LecLab]:
    return list(session.exec(select(LecLab).where(LecLab.section_id == section_id)))

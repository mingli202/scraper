import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select

from api.sections.cache import SectionCache
from api.sections.cache import load_section_cache
from api.sections.router import router as section_router
from scraper.db import SessionDep, init_db
from scraper.files import Files
from scraper.models import LecLab, LecLab, Rating, Rating

_ = load_dotenv()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    _app.state.section_cache = load_section_cache()
    yield


app = FastAPI(lifespan=lifespan)


env = os.environ.get("ENV", "DEV").upper()
print(f"env: {env}")

origin_regex: str = (
    r"https://dream-builder-hazel\.vercel\.app|https://dream-builder-\w+-vincents-projects-\w+\.vercel\.app|https://dream-builder-git-\w+-vincents-projects-\w+\.vercel\.app"
    if env == "PROD"
    else r".*"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=origin_regex,
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


@app.get("/ratings/{prof}", response_model=Rating)
def get_ratings(prof: str, request: Request, session: SessionDep) -> Rating:
    files = Files()

    ratings = files.read_ratings_responses()

    if ratings:
        rating = next((rating for rating in ratings if rating.prof == prof), None)
    else:
        section_cache = getattr(request.app.state, "section_cache", None)
        rating = None

        if isinstance(section_cache, SectionCache):
            for section in section_cache.all_sections:
                for leclab in section.leclabs:
                    if leclab.prof == prof and leclab.rating is not None:
                        rating = leclab.rating
                        break

                if rating is not None:
                    break

        if rating is None:
            db_rating = session.get(Rating, prof)
            if db_rating is not None:
                rating = Rating.model_validate(db_rating)

    if rating is None:
        raise HTTPException(status_code=404, detail=f"Rating for {prof} not found")

    return rating


@app.get("/leclab/{section_id}", response_model=list[LecLab])
def get_leclab(section_id: int, session: SessionDep) -> list[LecLab]:
    return list(session.exec(select(LecLab).where(LecLab.section_id == section_id)))

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from api.sections.cache import load_section_cache
from api.sections.helpers import load_ratings
from api.sections.router import router as section_router
from scraper.files import Files
from scraper.models import GlobalAllSections, Rating

_ = load_dotenv()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _app.state.section_cache = load_section_cache()
    _app.state.ratings = load_ratings()
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


@app.get("/global-all-sections")
async def get_global_all_sections() -> GlobalAllSections:
    files = Files()
    globalAllSections = files.get_global_all_sections_content()

    return globalAllSections


@app.get("/ratings/{prof}")
async def get_rating_prof(prof: str, request: Request) -> Rating:
    ratings = getattr(request.app.state, "ratings", None)
    if ratings is None:
        ratings = load_ratings()

    if prof not in ratings:
        raise HTTPException(
            status_code=400, detail=f"Rating for prof '{prof}' not found"
        )

    return ratings[prof]


@app.get("/ratings")
async def scrape_ratings() -> list[Rating]:
    return []

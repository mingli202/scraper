import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.sections.cache import load_section_cache
from api.sections.router import router as section_router

_ = load_dotenv()


@asynccontextmanager
async def lifespan(_app: FastAPI):
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

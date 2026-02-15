import os
from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine
from scraper.files import Files


file = Files()

sqlite_url = f"sqlite:///{file.all_sections_final_path}"
connect_args = {"check_same_thread": False}

engine = create_engine(
    sqlite_url, connect_args=connect_args, echo=os.environ.get("ENV", "DEV") != "PROD"
)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

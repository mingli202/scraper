import os
from typing import Annotated
from fastapi import Depends
from sqlalchemy import event
from sqlmodel import SQLModel, Session, create_engine
from .files import Files


file = Files()

sqlite_url = f"sqlite:///{file.all_sections_final_path}"
connect_args = {"check_same_thread": False}
env = os.environ.get("ENV", "PROD").upper()

engine = create_engine(
    sqlite_url,
    connect_args=connect_args,
    echo=env in {"DEV", "DEBUG"},
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA cache_size=-32000")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

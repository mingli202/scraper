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

INDEX_DDL = (
    'CREATE INDEX IF NOT EXISTS "ix_section_course" ON "section" ("course")',
    'CREATE INDEX IF NOT EXISTS "ix_section_domain" ON "section" ("domain")',
    'CREATE INDEX IF NOT EXISTS "ix_section_section" ON "section" ("section")',
    'CREATE INDEX IF NOT EXISTS "ix_section_code" ON "section" ("code")',
    'CREATE INDEX IF NOT EXISTS "ix_section_title" ON "section" ("title")',
    'CREATE INDEX IF NOT EXISTS "ix_section_more" ON "section" ("more")',
    'CREATE INDEX IF NOT EXISTS "ix_rating_score" ON "rating" ("score")',
    'CREATE INDEX IF NOT EXISTS "ix_rating_avg" ON "rating" ("avg")',
    'CREATE INDEX IF NOT EXISTS "ix_rating_status" ON "rating" ("status")',
    'CREATE INDEX IF NOT EXISTS "ix_leclab_prof" ON "leclab" ("prof")',
    'CREATE INDEX IF NOT EXISTS "ix_daytime_day" ON "daytime" ("day")',
    'CREATE INDEX IF NOT EXISTS "ix_daytime_start_time_hhmm" ON "daytime" ("start_time_hhmm")',
    'CREATE INDEX IF NOT EXISTS "ix_daytime_end_time_hhmm" ON "daytime" ("end_time_hhmm")',
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
    with engine.begin() as connection:
        for ddl in INDEX_DDL:
            connection.exec_driver_sql(ddl)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

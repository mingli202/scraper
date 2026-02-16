from sqlmodel import Session, select
from scraper.db import engine
from scraper.models import LecLab


if __name__ == "__main__":
    with Session(engine) as session:
        print(list(session.exec(select(LecLab).where(LecLab.section_id == 0))))

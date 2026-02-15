from sqlmodel import Session, select
from scraper.db import engine
from scraper.models import Section


if __name__ == "__main__":
    with Session(engine) as session:
        sections = session.exec(select(Section)).all()

        print(sections)

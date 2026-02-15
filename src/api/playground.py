from sqlmodel import Session, select
from scraper.db import engine
from scraper.models import Rating, Section


if __name__ == "__main__":
    with Session(engine) as session:
        print(session.exec(select(Section.section)).all())
        # print(session.exec(select(Rating)).all())

        # section = session.get(Section, 0)
        #
        # if section is not None:
        #     print(section)
        #     print(section.times)
        #
        #     for time in section.times:
        #         print(time.rating)

from sqlmodel import Session
from scraper.db import engine
from scraper.models import Section


if __name__ == "__main__":
    with Session(engine) as session:
        section = session.get(Section, 0)

        if section is not None:
            # print(section)
            # print(section.times)

            for time in section.times:
                print(time.rating)

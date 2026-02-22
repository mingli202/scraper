from sqlmodel import Session, select
from scraper.db import engine
from scraper.models import DayTime, LecLab, LecLabType, Rating, Section


def main():
    with Session(engine) as session:
        section = session.get(Section, 559)

        if section is None:
            return

        # print(section)
        # print(section.leclabs)
        #
        # print([leclab.day_times for leclab in section.leclabs])

        print(session.get(Rating, "Dupont, Sarah"))


if __name__ == "__main__":
    main()

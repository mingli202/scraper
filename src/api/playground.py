from sqlmodel import Session, select
from scraper.db import engine
from scraper.models import LecLab, Section


def main():
    with Session(engine) as session:
        section = session.get(Section, 0)

        if section is None:
            return


if __name__ == "__main__":
    main()

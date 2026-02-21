from sqlmodel import Session, select
from scraper.db import engine
from scraper.models import DayTime, LecLab, LecLabType, Section


def main():
    section = Section.default(
        section="00001",
        code="609-DAA-03",
        title="German I",
        leclabs=[
            LecLab.default(
                title="German I",
                prof="Siderova, Spaska",
                day_times=[
                    DayTime(
                        day="TR",
                        start_time_hhmm="1300",
                        end_time_hhmm="1430",
                    )
                ],
                type=LecLabType.LECTURE,
            )
        ],
    )

    print(section.leclabs)


# with Session(engine) as session:
#     section = session.get(Section, 0)
#
#     if section is None:
#         return


if __name__ == "__main__":
    main()

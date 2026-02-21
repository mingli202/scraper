from sqlmodel import and_, col, or_, select
from scraper.db import SessionDep
from scraper.models import LecLab, Rating, Section, Status


def filter_sections(
    session: SessionDep,
    q: str | None = None,
    course: str | None = None,
    domain: str | None = None,
    code: str | None = None,
    title: str | None = None,
    teacher: str | None = None,
    min_rating: int | None = None,
    max_rating: int | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
    days_off: str | None = None,
    time_start_query: str | None = None,
    time_end_query: str | None = None,
    blended: bool = False,
    honours: bool = False,
) -> list[Section]:
    statement = select(Section)

    if q is not None:
        statement = statement.where(
            or_(
                col(Section.title).ilike(f"%{q}%"),
                col(Section.course).ilike(f"{q}%"),
                col(Section.domain).ilike(f"{q}%"),
                col(Section.code).ilike(f"%{q}%"),
            )
        )

    if title is not None:
        statement = statement.where(col(Section.title).ilike(f"%{title}%"))

    if course is not None:
        statement = statement.where(col(Section.course).ilike(f"{course}%"))

    if domain is not None:
        statement = statement.where(col(Section.domain).ilike(f"{domain}%"))

    if code is not None:
        statement = statement.where(col(Section.code).ilike(f"%{code}%"))

    if blended:
        statement = statement.where(col(Section.more).ilike("BLENDED%"))

    if honours:
        statement = statement.where(col(Section.more).ilike("For Honours%"))

    if teacher:
        statement = statement.where(
            col(Section.leclabs).any(col(LecLab.prof).ilike(f"{teacher}%"))
        )

    if min_rating:
        statement = statement.where(
            ~col(Section.leclabs).any(
                ~col(LecLab.rating).has(
                    and_(Rating.status == Status.FOUND, Rating.avg < min_rating)
                )
            )
        )

    if max_rating:
        statement = statement.where(
            ~col(Section.leclabs).any(
                ~col(LecLab.rating).has(
                    and_(Rating.status == Status.FOUND, Rating.avg > max_rating)
                )
            )
        )

    if min_score:
        statement = statement.where(
            ~col(Section.leclabs).any(
                ~col(LecLab.rating).has(
                    and_(Rating.status == Status.FOUND, Rating.score < min_score)
                )
            )
        )

    if max_score:
        statement = statement.where(
            ~col(Section.leclabs).any(
                ~col(LecLab.rating).has(
                    and_(Rating.status == Status.FOUND, Rating.score > max_score)
                )
            )
        )

    sections = session.exec(statement)
    valid_sections: list[Section] = []

    for section in sections:
        leclabs = section.leclabs

        valid_time = True

        for leclab in leclabs:
            for d, t in leclab.time.items():
                if days_off is not None and any(_d in days_off for _d in d):
                    valid_time = False
                    break

                for t in t:
                    start_str, end_str = t.split("-")

                    if time_start_query is not None and int(start_str) < int(
                        time_start_query
                    ):
                        valid_time = False
                        break
                    if time_end_query is not None and int(end_str) > int(
                        time_end_query
                    ):
                        valid_time = False
                        break

                if not valid_time:
                    break

            if not valid_time:
                break

        if valid_time:
            section.leclabs = list(leclabs)
            valid_sections.append(section)

    return valid_sections

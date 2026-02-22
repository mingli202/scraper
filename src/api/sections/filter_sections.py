from sqlmodel import col, or_, select
from scraper.db import SessionDep
from scraper.models import DayTime, LecLab, Rating, Section, Status


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

    if q:
        statement = statement.where(
            or_(
                col(Section.title).ilike(f"%{q}%"),
                col(Section.course).ilike(f"{q}%"),
                col(Section.domain).ilike(f"{q}%"),
                col(Section.code).ilike(f"%{q}%"),
            )
        )

    if course is not None:
        statement = statement.where(col(Section.course).ilike(f"{course}%"))

    if domain is not None:
        statement = statement.where(col(Section.domain).ilike(f"{domain}%"))

    if code is not None:
        statement = statement.where(col(Section.code).ilike(f"%{code}%"))

    if title is not None:
        statement = statement.where(col(Section.title).ilike(f"%{title}%"))

    if blended:
        statement = statement.where(col(Section.more).ilike("BLENDED%"))

    if honours:
        statement = statement.where(col(Section.more).ilike("For Honours%"))

    if teacher is not None:
        statement = statement.where(
            col(Section.leclabs).any(col(LecLab.prof).icontains(teacher))
        )

    # there does not exist a leclab such that
    # rating.status != FOUND or rating.avg < min_rating
    if min_rating is not None:
        statement = statement.where(
            ~col(Section.leclabs).any(
                or_(
                    ~col(LecLab.rating).has(),
                    col(LecLab.rating).has(
                        or_(Rating.status != Status.FOUND, Rating.avg < min_rating)
                    ),
                )
            )
        )

    # there does not exist a leclab such that
    # rating.status != FOUND or rating.avg > max_rating
    if max_rating is not None:
        statement = statement.where(
            ~col(Section.leclabs).any(
                or_(
                    ~col(LecLab.rating).has(),
                    col(LecLab.rating).has(
                        or_(Rating.status != Status.FOUND, Rating.avg > max_rating)
                    ),
                )
            )
        )

    # there does not exist a leclab such that
    # rating.status != FOUND or rating.score < min_score
    if min_score is not None:
        statement = statement.where(
            ~col(Section.leclabs).any(
                or_(
                    ~col(LecLab.rating).has(),
                    col(LecLab.rating).has(
                        or_(Rating.status != Status.FOUND, Rating.score < min_score)
                    ),
                )
            )
        )

    # there does not exist a leclab such that
    # rating.status != FOUND or rating.score > max_score
    if max_score is not None:
        statement = statement.where(
            ~col(Section.leclabs).any(
                or_(
                    ~col(LecLab.rating).has(),
                    col(LecLab.rating).has(
                        or_(Rating.status != Status.FOUND, Rating.score > max_score)
                    ),
                )
            )
        )

    # there does not exist a leclab such that
    # there exist a day_time such that
    # at least one day_off is in day_time.day
    if days_off is not None:
        pattern = f"*[{days_off}]*"

        statement = statement.where(
            ~col(Section.leclabs).any(
                col(LecLab.day_times).any(or_(col(DayTime.day).op("GLOB")(pattern)))
            )
        )

    # there does not exist a leclab such that
    # there exist a day_time such that
    # day_time.start_time_hhmm < time_start_query
    if time_start_query is not None:
        statement = statement.where(
            ~col(Section.leclabs).any(
                col(LecLab.day_times).any(
                    col(DayTime.start_time_hhmm) < time_start_query
                )
            )
        )

    # there does not exist a leclab such that
    # there exist a day_time such that
    # day_time.end_time_hhmm > time_end_query
    if time_end_query is not None:
        statement = statement.where(
            ~col(Section.leclabs).any(
                col(LecLab.day_times).any(col(DayTime.end_time_hhmm) > time_end_query)
            )
        )

    sections = session.exec(statement).all()

    return list(sections)

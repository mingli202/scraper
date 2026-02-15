from sqlmodel import select
from scraper.db import SessionDep
from scraper.models import Section


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
            q in Section.title
            or q in Section.course
            or q in Section.domain
            or q in Section.code
        )

    if title is not None:
        statement = statement.where(title in Section.title)

    if course is not None:
        statement = statement.where(course in Section.course)

    if domain is not None:
        statement = statement.where(domain in Section.domain)

    if code is not None:
        statement = statement.where(code in Section.code)

    if blended:
        statement = statement.where(Section.more.startswith("BLENDED"))

    if honours:
        statement = statement.where(Section.more.startswith("For Honours"))

    sections = session.exec(statement)
    valid_sections: list[Section] = []

    for section in sections:
        leclabs = section.times

        valid_time = True

        if teacher is not None:
            valid_time = False
            for leclab in leclabs:
                if teacher.lower() in leclab.prof.lower():
                    valid_time = True
                    break

        if not valid_time:
            continue

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

            rating = leclab.rating

            if (
                min_rating is not None
                and rating.status == "found"
                and rating.avg < min_rating
            ):
                valid_time = False
                break
            if (
                max_rating is not None
                and rating.status == "found"
                and rating.avg > max_rating
            ):
                valid_time = False
                break

            if (
                min_score is not None
                and rating.status == "found"
                and rating.score < min_score
            ):
                valid_time = False
                break
            if (
                max_score is not None
                and rating.status == "found"
                and rating.score > max_score
            ):
                valid_time = False
                break

        if valid_time:
            section.times = list(leclabs)
            valid_sections.append(section)

    return valid_sections

from __future__ import annotations

from scraper.models import SectionResponse, Status


def _contains_ignore_case(value: str, query: str) -> bool:
    return query in value.lower()


def _starts_with_ignore_case(value: str, query: str) -> bool:
    return value.lower().startswith(query)


def _valid_rating_for_min(section: SectionResponse, min_rating: int) -> bool:
    for leclab in section.leclabs:
        rating = leclab.rating
        if rating is None or rating.status != Status.FOUND or rating.avg < min_rating:
            return False
    return True


def _valid_rating_for_max(section: SectionResponse, max_rating: int) -> bool:
    for leclab in section.leclabs:
        rating = leclab.rating
        if rating is None or rating.status != Status.FOUND or rating.avg > max_rating:
            return False
    return True


def _valid_score_for_min(section: SectionResponse, min_score: int) -> bool:
    for leclab in section.leclabs:
        rating = leclab.rating
        if rating is None or rating.status != Status.FOUND or rating.score < min_score:
            return False
    return True


def _valid_score_for_max(section: SectionResponse, max_score: int) -> bool:
    for leclab in section.leclabs:
        rating = leclab.rating
        if rating is None or rating.status != Status.FOUND or rating.score > max_score:
            return False
    return True


def filter_cached_sections(
    sections: tuple[SectionResponse, ...],
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
    limit: int | None = None,
    offset: int = 0,
) -> list[SectionResponse]:
    qv = q.lower() if q is not None else None
    coursev = course.lower() if course is not None else None
    domainv = domain.lower() if domain is not None else None
    codev = code.lower() if code is not None else None
    titlev = title.lower() if title is not None else None
    teacherv = teacher.lower() if teacher is not None else None

    filtered = sections

    if qv is not None:
        filtered = tuple(
            section
            for section in filtered
            if _contains_ignore_case(section.title, qv)
            or _starts_with_ignore_case(section.course, qv)
            or _starts_with_ignore_case(section.domain, qv)
            or _contains_ignore_case(section.code, qv)
        )

    if coursev is not None:
        filtered = tuple(
            section
            for section in filtered
            if _starts_with_ignore_case(section.course, coursev)
        )

    if domainv is not None:
        filtered = tuple(
            section
            for section in filtered
            if _starts_with_ignore_case(section.domain, domainv)
        )

    if codev is not None:
        filtered = tuple(
            section
            for section in filtered
            if _contains_ignore_case(section.code, codev)
        )

    if titlev is not None:
        filtered = tuple(
            section
            for section in filtered
            if _contains_ignore_case(section.title, titlev)
        )

    if blended:
        filtered = tuple(
            section for section in filtered if section.more.startswith("BLENDED")
        )

    if honours:
        filtered = tuple(
            section for section in filtered if section.more.startswith("For Honours")
        )

    if teacherv is not None:
        filtered = tuple(
            section
            for section in filtered
            if any(teacherv in leclab.prof.lower() for leclab in section.leclabs)
        )

    if min_rating is not None:
        filtered = tuple(
            section
            for section in filtered
            if _valid_rating_for_min(section, min_rating)
        )

    if max_rating is not None:
        filtered = tuple(
            section
            for section in filtered
            if _valid_rating_for_max(section, max_rating)
        )

    if min_score is not None:
        filtered = tuple(
            section for section in filtered if _valid_score_for_min(section, min_score)
        )

    if max_score is not None:
        filtered = tuple(
            section for section in filtered if _valid_score_for_max(section, max_score)
        )

    if days_off is not None:
        filtered = tuple(
            section
            for section in filtered
            if all(
                not any(day_off in day_time.day for day_off in days_off)
                for leclab in section.leclabs
                for day_time in leclab.day_times
            )
        )

    if time_start_query is not None:
        filtered = tuple(
            section
            for section in filtered
            if all(
                day_time.start_time_hhmm >= time_start_query
                for leclab in section.leclabs
                for day_time in leclab.day_times
            )
        )

    if time_end_query is not None:
        filtered = tuple(
            section
            for section in filtered
            if all(
                day_time.end_time_hhmm <= time_end_query
                for leclab in section.leclabs
                for day_time in leclab.day_times
            )
        )

    if offset > 0:
        filtered = filtered[offset:]

    if limit is not None:
        filtered = filtered[:limit]

    return list(filtered)

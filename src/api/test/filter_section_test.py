import itertools
from fastapi.testclient import TestClient
from pydantic import TypeAdapter
import pytest

from api.app import app
from scraper.models import SectionResponse


client = TestClient(app)


def _fetch_sections(params: dict[str, str | int]) -> list[SectionResponse]:
    res = client.get("/sections/", params=params)
    assert res.status_code == 200

    return TypeAdapter(list[SectionResponse]).validate_python(res.json())


@pytest.mark.parametrize(
    "q",
    [
        "calculus",
        "603-",
        "Science / Commerce",
        "psycholo",
        pytest.param("asdfqwer", marks=pytest.mark.xfail),
    ],
)
def test_filter_by_q(q: str):
    q = q.lower()
    res = client.get(f"/sections/?q={q}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())

    for section in sections:
        assert (
            q in section.title.lower()
            or q in section.course.lower()
            or q in section.domain.lower()
            or q in section.code.lower()
        )


@pytest.mark.parametrize(
    "course",
    [
        "Science",
        "Social",
        "Arts",
        "Com",
        pytest.param("calculus", marks=pytest.mark.xfail),
    ],
)
def test_filter_by_course(course: str):
    course = course.lower()
    res = client.get(f"/sections/?course={course}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())

    for section in sections:
        assert section.course.lower().startswith(course)


@pytest.mark.parametrize(
    "domain",
    [
        "biology",
        "psy",
        "huma",
        "POLITICAL",
        pytest.param("calculus", marks=pytest.mark.xfail),
    ],
)
def test_filter_by_domain(domain: str):
    domain = domain.lower()
    res = client.get(f"/sections/?domain={domain}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())

    for section in sections:
        assert section.domain.lower().startswith(domain)


@pytest.mark.parametrize(
    "title",
    [
        "biology",
        "psy",
        "huma",
        "calculus",
        pytest.param("chinese new year", marks=pytest.mark.xfail),
    ],
)
def test_filter_by_title(title: str):
    title = title.lower()
    res = client.get(f"/sections/?title={title}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())

    for section in sections:
        assert title in section.title.lower()


@pytest.mark.parametrize(
    "code",
    [
        "603",
        "103",
        "MQ",
        "300-SLA",
        pytest.param("chinese new year", marks=pytest.mark.xfail),
    ],
)
def test_filter_by_code(code: str):
    code = code.lower()
    res = client.get(f"/sections/?code={code}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())

    for section in sections:
        assert code in section.code.lower()


@pytest.mark.parametrize(
    "teacher",
    [
        "Abray",
        "Lawrence",
        "Xiao",
        "Chris",
        pytest.param("chinese new year", marks=pytest.mark.xfail),
    ],
)
def test_filter_by_teacher(teacher: str):
    teacher = teacher.lower()
    res = client.get(f"/sections/?teacher={teacher}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())

    for section in sections:
        assert any(teacher in leclab.prof.lower() for leclab in section.leclabs)


@pytest.mark.parametrize(
    "min_rating",
    [0, 2, 4, 5, 9, -1, pytest.param(3.1, marks=pytest.mark.xfail)],
)
def test_filter_by_min_rating(min_rating: int):
    res = client.get(f"/sections/?min_rating={min_rating}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())
    leclabs = itertools.chain.from_iterable(section.leclabs for section in sections)
    ratings = [leclab.rating for leclab in leclabs]

    assert all(rating is not None and rating.avg >= min_rating for rating in ratings)


@pytest.mark.parametrize(
    "max_rating",
    [0, 2, 4, 5, 9, -1, pytest.param(3.1, marks=pytest.mark.xfail)],
)
def test_filter_by_max_rating(max_rating: int):
    res = client.get(f"/sections/?max_rating={max_rating}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())
    leclabs = itertools.chain.from_iterable(section.leclabs for section in sections)
    ratings = [leclab.rating for leclab in leclabs]

    assert all(rating is not None and rating.avg <= max_rating for rating in ratings)


@pytest.mark.parametrize(
    "min_score",
    [0, 21, 39, 54, 95, -1, pytest.param(3.1, marks=pytest.mark.xfail)],
)
def test_filter_by_min_score(min_score: int):
    res = client.get(f"/sections/?min_score={min_score}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())
    leclabs = itertools.chain.from_iterable(section.leclabs for section in sections)
    ratings = [leclab.rating for leclab in leclabs]

    assert all(rating is not None and rating.score >= min_score for rating in ratings)


@pytest.mark.parametrize(
    "max_score",
    [0, 21, 39, 54, 95, -1, pytest.param(3.1, marks=pytest.mark.xfail)],
)
def test_filter_by_max_score(max_score: int):
    res = client.get(f"/sections/?max_score={max_score}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())
    leclabs = itertools.chain.from_iterable(section.leclabs for section in sections)
    ratings = [leclab.rating for leclab in leclabs]

    assert all(rating is not None and rating.score <= max_score for rating in ratings)


@pytest.mark.parametrize(
    "days_off", ["M", "MTW", "MF", "WR", pytest.param("", marks=pytest.mark.xfail)]
)
def test_filter_by_days_off(days_off: str):
    res = client.get(f"/sections/?days_off={days_off}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())
    leclabs = itertools.chain.from_iterable(section.leclabs for section in sections)
    day_times = itertools.chain.from_iterable(leclab.day_times for leclab in leclabs)

    assert all(
        not any(day_off in day_time.day for day_off in days_off)
        for day_time in day_times
    )


@pytest.mark.parametrize(
    "time_start",
    [
        "0900",
        "0000",
        "2400",
        "1200",
        "1030",
        "1449",
        pytest.param("", marks=pytest.mark.xfail),
    ],
)
def test_filter_by_time_start(time_start: str):
    res = client.get(f"/sections/?time_start={time_start}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())
    leclabs = itertools.chain.from_iterable(section.leclabs for section in sections)
    day_times = itertools.chain.from_iterable(leclab.day_times for leclab in leclabs)

    for day_time in day_times:
        assert day_time.start_time_hhmm >= time_start


@pytest.mark.parametrize(
    "time_end",
    [
        "0900",
        "0000",
        "2400",
        "1200",
        "1030",
        "1449",
        pytest.param("", marks=pytest.mark.xfail),
    ],
)
def test_filter_by_time_end(time_end: str):
    res = client.get(f"/sections/?time_end={time_end}")
    assert res.status_code == 200
    sections = TypeAdapter(list[SectionResponse]).validate_python(res.json())
    leclabs = itertools.chain.from_iterable(section.leclabs for section in sections)
    day_times = itertools.chain.from_iterable(leclab.day_times for leclab in leclabs)

    for day_time in day_times:
        assert day_time.end_time_hhmm <= time_end


@pytest.mark.parametrize(
    "query_steps",
    [
        [
            {"course": "science"},
            {"course": "science", "domain": "biology"},
            {"course": "science", "domain": "biology", "min_rating": 2},
            {"course": "science", "domain": "biology", "min_rating": 2, "days_off": "M"},
            {
                "course": "science",
                "domain": "biology",
                "min_rating": 2,
                "days_off": "M",
                "time_start": "0900",
            },
            {
                "course": "science",
                "domain": "biology",
                "min_rating": 2,
                "days_off": "M",
                "time_start": "0900",
                "time_end": "1800",
            },
        ],
        [
            {"q": "calculus"},
            {"q": "calculus", "course": "science"},
            {"q": "calculus", "course": "science", "domain": "mathematics"},
            {
                "q": "calculus",
                "course": "science",
                "domain": "mathematics",
                "min_score": 39,
            },
            {
                "q": "calculus",
                "course": "science",
                "domain": "mathematics",
                "min_score": 39,
                "days_off": "F",
            },
            {
                "q": "calculus",
                "course": "science",
                "domain": "mathematics",
                "min_score": 39,
                "days_off": "F",
                "time_end": "1700",
            },
        ],
    ],
)
def test_filter_by_multiple_params_narrows_progressively(
    query_steps: list[dict[str, str | int]],
):
    result_ids = [{section.id for section in _fetch_sections(params)} for params in query_steps]

    for previous, current in zip(result_ids, result_ids[1:]):
        assert current.issubset(previous)

    assert any(
        len(current) < len(previous)
        for previous, current in zip(result_ids, result_ids[1:])
    )
    assert len(result_ids[-1]) > 0


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-v", __file__]))

from fastapi.testclient import TestClient
from pydantic import TypeAdapter
import pytest

from api.app import app
from scraper.models import SectionResponse


client = TestClient(app)


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


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-v", __file__]))

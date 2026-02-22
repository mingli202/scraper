from fastapi.testclient import TestClient
from pydantic import TypeAdapter
import pytest

from api.app import app
from scraper.models import SectionResponse


client = TestClient(app)


@pytest.mark.parametrize("q", ["calculus", "603-", "Science / Commerce", "psycholo"])
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


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-vvv", __file__]))

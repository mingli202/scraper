from typing import Any
import pytest
from api.app import app
from fastapi.testclient import TestClient

from scraper.models import (
    DayTime,
    LecLab,
    LecLabType,
    Rating,
    Section,
    SectionResponse,
    Status,
)

client = TestClient(app)


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"message": "Hello World!"}


def test_get_all_sections():
    res = client.get("/sections/")
    assert res.status_code == 200
    assert len(res.json()) > 900


def test_get_section():
    res = client.get("/sections/1")
    assert res.status_code == 200
    section = SectionResponse.model_validate(res.json())

    assert section.course == "Science Courses"
    assert section.section == "00002"
    assert section.domain == "BIOLOGY"
    assert section.code == "101-SN1-RE"
    assert section.title == "Cellular Biology"
    assert section.more == ""
    assert section.view_data == [{"4": [4, 8]}, {"2": [14, 18]}]

    assert len(section.leclabs) == 2

    l1, l2 = section.leclabs
    assert l1.section_id == l2.section_id == 1
    assert l1.title == l2.title == "Cellular Biology"

    assert l1.type == LecLabType.LECTURE
    assert l1.prof == "Dupont, Sarah"
    assert len(l1.day_times) == 1
    assert l1.day_times[0].day == "R"
    assert l1.day_times[0].start_time_hhmm == "0930"
    assert l1.day_times[0].end_time_hhmm == "1130"

    assert l2.type == LecLabType.LAB
    assert l2.prof == "Rioux, Marie-Claire"
    assert len(l2.day_times) == 1
    assert l2.day_times[0].day == "T"
    assert l2.day_times[0].start_time_hhmm == "1430"
    assert l2.day_times[0].end_time_hhmm == "1630"


@pytest.mark.parametrize("id", [-1, 10000, "nan", None])
def test_get_section_invalid(id: Any):
    res = client.get(f"/sections/{id}")
    assert res.status_code != 200


def test_get_rating():
    res = client.get("/ratings/Hughes, Cameron")
    assert res.status_code == 200
    rating = Rating.model_validate(res.json())
    assert rating == Rating(
        prof="Hughes, Cameron",
        avg=3.8,
        score=71.7,
        difficulty=3.5,
        nRating=10,
        takeAgain=60,
        status=Status.FOUND,
        pId="2984556",
    )


@pytest.mark.parametrize("prof", [123, "oweiruoweiurjl", None])
def test_get_rating_invalid(prof: Any):
    res = client.get(f"/ratings/{prof}")
    assert res.status_code != 200


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-vvv", __file__]))

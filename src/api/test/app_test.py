from typing import Any
import pytest
from api.app import app
from fastapi.testclient import TestClient

from scraper.models import LecLab, LecLabType, Rating, Section, Status

client = TestClient(app)


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"message": "Hello World!"}


def test_get_all_sections():
    res = client.get("/sections/")
    assert res.status_code == 200
    assert len(res.json()) > 900
    first_section = Section.model_validate(res.json()[0])
    assert first_section == Section(
        id=0,
        course="Science Courses",
        section="00001",
        domain="BIOLOGY",
        code="101-SN1-RE",
        title="Cellular Biology",
        leclabs=[
            LecLab(
                section_id=0,
                title="Cellular Biology",
                type=LecLabType.LECTURE,
                prof="Dupont, Sarah",
                time={"R": ["0930-1130"]},
            ),
            LecLab(
                section_id=0,
                title="Cellular Biology",
                type=LecLabType.LAB,
                prof="Hughes, Cameron",
                time={"T": ["1230-1430"]},
            ),
        ],
        more="",
        view_data=[{"4": [4, 8]}, {"2": [10, 14]}],
    )


def test_get_section():
    res = client.get("/sections/1")
    assert res.status_code == 200
    section = Section.model_validate(res.json())
    assert section == Section(
        id=1,
        course="Science Courses",
        section="00002",
        domain="BIOLOGY",
        code="101-SN1-RE",
        title="Cellular Biology",
        leclabs=[
            LecLab(
                section_id=1,
                title="Cellular Biology",
                type=LecLabType.LAB,
                prof="Dupont, Sarah",
                time={"R": ["0930-1130"]},
            ),
            LecLab(
                section_id=1,
                title="Cellular Biology",
                type=LecLabType.LECTURE,
                prof="Rioux, Marie-Claire",
                time={"T": ["1430-1630"]},
            ),
        ],
        more="",
        view_data=[{"4": [4, 8]}, {"2": [14, 18]}],
    )


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

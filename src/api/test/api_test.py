import pytest
from api.app import app
from fastapi.testclient import TestClient

from scraper.models import LecLab, Section

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
        times=[
            LecLab(
                title="Cellular Biology",
                type="lecture",
                prof="Dupont, Sarah",
                time={"R": ["0930-1130"]},
            ),
            LecLab(
                title="Cellular Biology",
                type="laboratory",
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
        times=[
            LecLab(
                title="Cellular Biology",
                type="lecture",
                prof="Dupont, Sarah",
                time={"R": ["0930-1130"]},
            ),
            LecLab(
                title="Cellular Biology",
                type="laboratory",
                prof="Rioux, Marie-Claire",
                time={"T": ["1430-1630"]},
            ),
        ],
        more="",
        view_data=[{"4": [4, 8]}, {"2": [14, 18]}],
    )


def test_get_section_invalid():
    res = client.get("/sections/10000")
    assert res.status_code == 200
    assert res.json() is None


if __name__ == "__main__":
    exit(pytest.main(["-s", "-v", __file__]))

from typing import Any
import pytest
from api.app import app
from api.sections import router as section_router
from fastapi.testclient import TestClient

from scraper.models import (
    DayTime,
    LecLab,
    LecLabType,
    Rating,
    Section,
    Status,
)

client = TestClient(app)


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"message": "Hello World!"}


def test_get_all_sections_without_filters_returns_empty():
    res = client.get("/sections/")
    assert res.status_code == 200
    assert res.json() == []


def test_parse_uploaded_pdf_rejects_non_pdf():
    res = client.post(
        "/sections/parse-pdf",
        files={"file": ("schedule.txt", b"not a pdf", "text/plain")},
    )

    assert res.status_code == 400


def test_parse_uploaded_pdf_returns_sections_schema(monkeypatch: pytest.MonkeyPatch):
    class FakeFiles:
        def __init__(self, pdf_path):
            self.data_dir = pdf_path.parent / "fake-parser-data"

    class FakeParser:
        def __init__(self, _files: FakeFiles):
            day_time = DayTime(
                day="M",
                start_time_hhmm="0900",
                end_time_hhmm="1100",
            )
            leclab = LecLab(
                title="Calculus I",
                type=LecLabType.LECTURE,
                prof="Doe, Jane",
                day_times=[day_time],
            )
            section = Section(
                course="Science Courses",
                section="00001",
                domain="MATHEMATICS",
                code="201-NYA-05",
                title="Calculus I",
                more="",
                view_data=[{"0": [0, 2]}],
                leclabs=[leclab],
            )
            self.sections = [section]

        def parse(self):
            return

    monkeypatch.setattr(section_router, "Files", FakeFiles)
    monkeypatch.setattr(section_router, "NewParser", FakeParser)

    res = client.post(
        "/sections/parse-pdf",
        files={"file": ("schedule.pdf", b"%PDF-1.7\nfake", "application/pdf")},
    )
    assert res.status_code == 200

    sections = [Section.model_validate(section) for section in res.json()]
    assert len(sections) == 1
    assert sections[0].code == "201-NYA-05"
    assert sections[0].leclabs[0].day_times[0].start_time_hhmm == "0900"


def test_get_section():
    res = client.get("/sections/1")
    assert res.status_code == 200
    section = Section.model_validate(res.json())

    assert section.course == "Science Courses"
    assert section.section == "00002"
    assert section.domain == "BIOLOGY"
    assert section.code == "101-SN1-RE"
    assert section.title == "Cellular Biology"
    assert section.more == ""
    assert section.view_data == [{"4": [4, 8]}, {"2": [14, 18]}]

    assert len(section.leclabs) == 2

    l1, l2 = section.leclabs
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

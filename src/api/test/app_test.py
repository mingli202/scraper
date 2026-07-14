from typing import Any
import pytest
from api.app import app
from api.sections import router as section_router
from fastapi.testclient import TestClient

from scraper.models import (
    DayTime,
    GlobalAllSections,
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
    def fake_parse(_pdf_path, _ratings, max_pages):
        assert max_pages == section_router.MAX_PDF_PAGES
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
        return GlobalAllSections(
            semester="FALL 2026",
            sections_by_id={"201-NYA-05-00001": section},
            filename="schedule.pdf",
            sections_diff=None,
            comments=[],
        )

    monkeypatch.setattr(section_router, "the_entire_loop", fake_parse)

    res = client.post(
        "/sections/parse-pdf",
        files={"file": ("schedule.pdf", b"%PDF-1.7\nfake", "application/pdf")},
    )
    assert res.status_code == 200

    sections = [
        Section.model_validate(section)
        for section in res.json()["sectionsById"].values()
    ]
    assert len(sections) == 1
    assert sections[0].code == "201-NYA-05"
    assert sections[0].leclabs[0].day_times[0].start_time_hhmm == "0900"


def test_parse_uploaded_pdf_rejects_oversized_upload(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(section_router, "MAX_PDF_UPLOAD_BYTES", 10)

    res = client.post(
        "/sections/parse-pdf",
        files={"file": ("schedule.pdf", b"%PDF-1.7\n123", "application/pdf")},
    )

    assert res.status_code == 413


def test_get_section():
    res = client.get("/sections/101-SN1-RE-00002")
    assert res.status_code == 200
    section = Section.model_validate(res.json())

    assert section.course == "Science Courses"
    assert section.section == "00002"
    assert section.domain == "BIOLOGY"
    assert section.code == "101-SN1-RE"
    assert section.title == "Cellular Biology"
    assert section.more == ""

    assert len(section.leclabs) == 2

    l1, l2 = section.leclabs
    assert l1.title == l2.title == "Cellular Biology"


@pytest.mark.parametrize("id", [-1, 10000, "nan", None])
def test_get_section_invalid(id: Any):
    res = client.get(f"/sections/{id}")
    assert res.status_code != 200


def test_get_rating():
    res = client.get("/ratings/Hughes, Cameron")
    assert res.status_code == 200
    rating = Rating.model_validate(res.json())
    assert rating.prof == "Hughes, Cameron"
    assert rating.pId == "2984556"
    assert rating.status == Status.FOUND


@pytest.mark.parametrize("prof", [123, "oweiruoweiurjl", None])
def test_get_rating_invalid(prof: Any):
    res = client.get(f"/ratings/{prof}")
    assert res.status_code != 200


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-vvv", __file__]))

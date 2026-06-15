import pytest

from scraper.models import DayTime, LecLab, Rating, Section
from scraper.util import is_different


@pytest.mark.parametrize(
    "old_section,new_section,res",
    [
        (
            Section(id="1", code="1", leclabs=[LecLab(prof="prof 1")]),
            Section(id="1", code="1", leclabs=[LecLab(prof="prof 1")]),
            False,
        ),
        (
            Section(id="1", code="1", leclabs=[LecLab(prof="prof 1")]),
            Section(id="1", code="1", leclabs=[LecLab(prof="prof 2")]),
            True,
        ),
        (
            Section(
                id="1",
                code="1",
                leclabs=[LecLab(prof="prof 1", day_times=[DayTime(day="M")])],
            ),
            Section(
                id="1",
                code="1",
                leclabs=[LecLab(prof="prof 1", day_times=[DayTime(day="T")])],
            ),
            True,
        ),
        (
            Section(
                id="1",
                code="1",
                leclabs=[LecLab(prof="prof 1", rating=Rating(prof="prof 1", score=1))],
            ),
            Section(
                id="1",
                code="1",
                leclabs=[LecLab(prof="prof 1", rating=Rating(prof="prof 1", score=2))],
            ),
            False,
        ),
    ],
)
def test_is_different_prof(old_section: Section, new_section: Section, res: bool):
    assert is_different(old_section, new_section) == res


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-vvv", __file__]))

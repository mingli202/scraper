import pytest

from scraper.models import (
    DayTime,
    GlobalAllSections,
    LecLab,
    Rating,
    Section,
    SectionsDiff,
)
from scraper.util import get_global_sections_diff, get_sections_diff, is_different


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


def test_global_diff_different_semester():
    old_global = GlobalAllSections(
        semester="fall 2026",
        filename="",
        sections_diff=SectionsDiff(
            previous_sections_changed=[], sections_added=[], sections_removed=[]
        ),
        sections_by_id={},
    )

    assert get_global_sections_diff("winter", old_global, {}) is None


@pytest.mark.parametrize(
    "old_sections,new_sections,diff",
    [
        (
            {
                "1": Section(id="1", title="asdf"),
                "2": Section(id="2", title="qwer"),
                "3": Section(id="3", title="asdf"),
            },
            {
                "1": Section(id="1", title="asdf"),
                "2": Section(id="2", title="asdf"),
                "4": Section(id="4", title="asdf"),
            },
            SectionsDiff(
                previous_sections_changed=[Section(id="2", title="qwer")],
                sections_added=["4"],
                sections_removed=[Section(id="3", title="asdf")],
            ),
        ),
    ],
)
def test_section_diff(
    old_sections: dict[str, Section],
    new_sections: dict[str, Section],
    diff: SectionsDiff,
):
    assert get_sections_diff(old_sections, new_sections) == diff


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-vvv", __file__]))

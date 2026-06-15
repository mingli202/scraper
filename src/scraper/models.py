from enum import Enum
import logging
from typing import Any, override

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

logger = logging.getLogger(__name__)


type ViewData = list[dict[str, list[int]]]


class Status(str, Enum):
    FOUND = "found"
    FOUNDNT = "foundn't"


class LecLabType(str, Enum):
    LECTURE = "lecture"
    LAB = "laboratory"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )


class DayTime(ConfiguredBaseModel):
    day: str = ""
    start_time_hhmm: str = ""
    end_time_hhmm: str = ""


class Rating(ConfiguredBaseModel):
    prof: str
    score: float = 0
    avg: float = 0
    nRating: int = 0
    takeAgain: int = 0
    difficulty: float = 0
    status: Status = Status.FOUNDNT
    pId: str | None = None


class LecLab(ConfiguredBaseModel):
    title: str = ""
    type: LecLabType | None = None
    prof: str = ""
    rating: Rating | None = None
    day_times: list[DayTime] = []

    def update_time(self, day: str, start_time: str, end_time: str):
        day_time = DayTime(
            day=day,
            start_time_hhmm=start_time,
            end_time_hhmm=end_time,
        )

        self.day_times.append(day_time)


class Section(ConfiguredBaseModel):
    id: str = ""  # unique Id for this section made of the code + section number
    course: str = ""
    section: str = ""
    domain: str = ""
    code: str = ""
    title: str = ""
    leclabs: list[LecLab] = []
    more: str = ""
    view_data: ViewData = []


class ColumnsXs(BaseModel):
    section: int
    disc: int
    course_number: int
    course_title: int
    day: int
    time: int


class Word(BaseModel):
    page_number: int
    text: str
    x0: int
    top: int
    doctop: int

    @override
    def __hash__(self):
        return hash(self.model_dump_json(by_alias=True))


class SectionsDiff(ConfiguredBaseModel):
    sections_diff: dict[str, SectionDiff]
    sections_added: list[str]
    sections_removed: list[str]


class Diff(ConfiguredBaseModel):
    old: str
    new: str


class SectionDiff(ConfiguredBaseModel):
    sectionId: str
    diffs: list[Diff]


class GlobalAllSections(ConfiguredBaseModel):
    semester: str
    filename: str
    sections_diff: SectionsDiff | None
    sections_by_id: dict[str, Section]

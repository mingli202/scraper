from enum import Enum
import logging
from typing import Self, override

from pydantic import BaseModel
from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel

logger = logging.getLogger(__name__)


type Time = dict[str, list[str]]  # day: list["HHMM-HHMM"]
type ViewData = list[dict[str, list[int]]]


class Status(str, Enum):
    FOUND = "found"
    FOUNDNT = "foundn't"


class LecLabType(str, Enum):
    LECTURE = "lecture"
    LAB = "laboratory"


class Section(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, index=True)

    course: str = Field(default="")
    section: str = Field(default="")
    domain: str = Field(default="")
    code: str = Field(default="")
    title: str = Field(default="")
    more: str = Field(default="")
    view_data: ViewData = Field(default_factory=list, sa_type=JSON)

    times: list["LecLab"] = Relationship(back_populates="section")


class Rating(SQLModel, table=True):
    prof: str = Field(default=None, primary_key=True, index=True)

    score: float = Field(default=0.0)
    avg: float = Field(default=0)
    nRating: int = Field(default=0)
    takeAgain: int = Field(default=0)
    difficulty: float = Field(default=0)
    status: Status = Field(default=Status.FOUNDNT)
    pId: str | None = Field(default=None)

    leclabs: list["LecLab"] = Relationship(back_populates="rating")


class LecLab(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)

    title: str = Field(default="")
    type: LecLabType | None = Field(default=None)
    time: Time = Field(default_factory=dict, sa_type=JSON)

    section_id: int = Field(default=None, index=True, foreign_key="section.id")
    prof: str = Field(default="", foreign_key="rating.prof")

    section: Section = Relationship(back_populates="times")
    rating: Rating = Relationship(back_populates="leclabs")

    def update(self, tmp: Self):
        if tmp.title != "":
            self.title = tmp.title

        if tmp.prof != "":
            self.prof = tmp.prof

        self.update_time(tmp.time)

    def update_time(self, tmp: Time):
        for k, v in tmp.items():
            self.time.setdefault(k, []).extend(v)

        for times in self.time.values():
            for i, time1 in enumerate(times):
                start1, end1 = time1.split("-")
                start1 = int(start1)
                end1 = int(end1)

                for times2 in times[i + 1 :]:
                    start2, end2 = times2.split("-")
                    start2 = int(start2)
                    end2 = int(end2)

                    if start1 > end2 or start2 > end1:
                        logger.warning("overlapping times")

    def clear(self):
        self.title = ""
        self.type = None
        self.prof = ""
        self.time = {}


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

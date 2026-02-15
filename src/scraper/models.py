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
    id: int = Field(primary_key=True, index=True)

    course: str = Field()
    section: str = Field()
    domain: str = Field()
    code: str = Field()
    title: str = Field()
    more: str = Field()
    view_data: ViewData = Field(sa_type=JSON)

    times: list["LecLab"] = Relationship(back_populates="section")

    @classmethod
    def default(cls) -> Section:
        return Section(
            id=0,
            course="",
            section="",
            domain="",
            code="",
            title="",
            more="",
            view_data=[],
        )


class Rating(SQLModel, table=True):
    prof: str = Field(primary_key=True, index=True)

    score: float = Field()
    avg: float = Field()
    nRating: int = Field()
    takeAgain: int = Field()
    difficulty: float = Field()
    status: Status = Field()
    pId: str | None = Field()

    leclabs: list["LecLab"] = Relationship(back_populates="rating")

    @classmethod
    def default(cls) -> Rating:
        return Rating(
            prof="",
            score=0,
            avg=0,
            nRating=0,
            takeAgain=0,
            difficulty=0,
            status=Status.FOUNDNT,
            pId=None,
        )


class LecLab(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)

    title: str = Field()
    type: LecLabType | None = Field()
    time: Time = Field(sa_type=JSON)

    section_id: int = Field(index=True, foreign_key="section.id")
    prof: str = Field(foreign_key="rating.prof")

    section: Section = Relationship(back_populates="times")
    rating: Rating = Relationship(back_populates="leclabs")

    @classmethod
    def default(cls) -> LecLab:
        return LecLab(title="", type=None, time=dict(), section_id=0, prof="")

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

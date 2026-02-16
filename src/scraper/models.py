from enum import Enum
import logging
from typing import Self, override

from pydantic import BaseModel
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped
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
    id: Mapped[int] = Field(primary_key=True, index=True)

    course: Mapped[str] = Field()
    section: Mapped[str] = Field()
    domain: Mapped[str] = Field()
    code: Mapped[str] = Field()
    title: Mapped[str] = Field()
    more: Mapped[str] = Field()
    view_data: Mapped[ViewData] = Field(sa_type=JSON)

    times: Mapped[list["LecLab"]] = Relationship(back_populates="section")

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
            times=[],
        )


class Rating(SQLModel, table=True):
    prof: Mapped[str] = Field(primary_key=True, index=True)

    score: Mapped[float] = Field()
    avg: Mapped[float] = Field()
    nRating: Mapped[int] = Field()
    takeAgain: Mapped[int] = Field()
    difficulty: Mapped[float] = Field()
    status: Mapped[Status] = Field()
    pId: Mapped[str | None] = Field()

    leclabs: Mapped[list["LecLab"]] = Relationship(back_populates="rating")

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
            leclabs=[],
        )


class LecLab(SQLModel, table=True):
    id: Mapped[int] = Field(default=None, primary_key=True)

    title: Mapped[str] = Field()
    type: Mapped[LecLabType | None] = Field()
    time: Mapped[Time] = Field(sa_type=JSON)

    section_id: Mapped[int] = Field(index=True, foreign_key="section.id")
    prof: Mapped[str] = Field(foreign_key="rating.prof")

    section: Mapped[Section] = Relationship(back_populates="times")
    rating: Mapped[Rating] = Relationship(back_populates="leclabs")

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

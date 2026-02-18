from enum import Enum
import logging
from typing import Self, override

from pydantic import BaseModel
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, SQLModel

logger = logging.getLogger(__name__)


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

    leclabs: Mapped[list["LecLab"]] = Relationship(back_populates="section")

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
            leclabs=[],
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

    section_id: Mapped[int] = Field(index=True, foreign_key="section.id")
    prof: Mapped[str] = Field(foreign_key="rating.prof")

    section: Mapped[Section] = Relationship(back_populates="leclabs")
    rating: Mapped[Rating | None] = Relationship(back_populates="leclabs")
    day_times: Mapped[list[DayTime]] = Relationship(back_populates="leclab")

    @classmethod
    def default(cls) -> LecLab:
        return LecLab(title="", type=None, section_id=0, prof="")

    def update(self, tmp: Self):
        if tmp.title != "":
            self.title = tmp.title

        if tmp.prof != "":
            self.prof = tmp.prof

        self.day_times.extend(tmp.day_times)

    def update_time(self, day: str, start_time: str, end_time: str):
        day_time = DayTime(
            day=day,
            start_time_hhmm=start_time,
            end_time_hhmm=end_time,
        )

        self.day_times.append(day_time)


class DayTime(SQLModel, table=True):
    id: Mapped[int] = Field(default=None, primary_key=True)

    leclab_id: Mapped[int] = Field(default=None, foreign_key="leclab.id", index=True)
    leclab: Mapped[LecLab] = Relationship(back_populates="times")

    day: Mapped[str] = Field()
    start_time_hhmm: Mapped[str] = Field()
    end_time_hhmm: Mapped[str] = Field()


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

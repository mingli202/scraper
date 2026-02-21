from enum import Enum
import logging
from typing import Self, override

from pydantic import BaseModel
from sqlalchemy import JSON
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
    id: int = Field(primary_key=True, index=True)

    course: str = Field()
    section: str = Field()
    domain: str = Field()
    code: str = Field()
    title: str = Field()
    more: str = Field()
    view_data: ViewData = Field(sa_type=JSON)

    leclabs: list[LecLab] = Relationship(
        back_populates="section", sa_relationship_kwargs={"lazy": "selectin"}
    )

    @classmethod
    def default(
        cls,
        id: int = 0,
        course: str = "",
        section: str = "",
        domain: str = "",
        code: str = "",
        title: str = "",
        more: str = "",
        view_data: ViewData | None = None,
        leclabs: list[LecLab] | None = None,
    ) -> Section:
        return Section(
            id=id,
            course=course,
            section=section,
            domain=domain,
            code=code,
            title=title,
            more=more,
            view_data=view_data if view_data is not None else [],
            leclabs=leclabs if leclabs is not None else [],
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

    leclabs: list[LecLab] = Relationship(back_populates="rating")

    @classmethod
    def default(
        cls,
        prof: str = "",
        score: int = 0,
        avg: float = 0.0,
        nRating: int = 0,
        takeAgain: int = 0,
        difficulty: float = 0.0,
        status: Status = Status.FOUNDNT,
        pId: str | None = None,
        leclabs: list[LecLab] | None = None,
    ) -> Rating:
        return Rating(
            prof=prof,
            score=score,
            avg=avg,
            nRating=nRating,
            takeAgain=takeAgain,
            difficulty=difficulty,
            status=status,
            pId=pId,
            leclabs=leclabs if leclabs is not None else [],
        )


class LecLab(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)

    title: str = Field()
    type: LecLabType | None = Field()

    section_id: int = Field(index=True, foreign_key="section.id")
    prof: str = Field(foreign_key="rating.prof")

    section: Section = Relationship(back_populates="leclabs")
    rating: Rating | None = Relationship(back_populates="leclabs")
    day_times: list[DayTime] = Relationship(back_populates="leclab")

    @classmethod
    def default(
        cls,
        title: str = "",
        type: LecLabType | None = None,
        section_id: int = 0,
        prof: str = "",
        day_times: list[DayTime] | None = None,
    ) -> LecLab:
        return LecLab(
            title=title,
            type=type,
            section_id=section_id,
            prof=prof,
            day_times=day_times if day_times is not None else [],
        )

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
    id: int = Field(default=None, primary_key=True)

    day: str = Field()
    start_time_hhmm: str = Field()
    end_time_hhmm: str = Field()
    leclab_id: int = Field(default=None, foreign_key="leclab.id", index=True)

    leclab: LecLab = Relationship(back_populates="day_times")


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

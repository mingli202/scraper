import logging
from sqlite3 import Cursor
from typing import Any, Literal, Self, override

from pydantic import BaseModel, TypeAdapter
from sqlmodel import Field, SQLModel

logger = logging.getLogger(__name__)


type Time = dict[str, list[str]]  # day: list["HHMM-HHMM"]
type ViewData = list[dict[str, list[int]]]


class Rating(SQLModel, table=True):
    prof: str = Field(default="", primary_key=True, index=True)
    score: float = Field(default=0.0)
    avg: float = Field(default=0)
    nRating: int = Field(default=0)
    takeAgain: int = Field(default=0)
    difficulty: float = Field(default=0)
    status: Literal["found", "foundn't"] = Field(default="foundn't")
    pId: str | None = Field(default=None)

    @classmethod
    def validate_db_response(cls, db_response: Any) -> Rating:
        adapter = TypeAdapter(
            tuple[
                str,
                float,
                float,
                int,
                int,
                float,
                Literal["found", "foundn't"],
                str | None,
            ]
        )
        prof, score, avg, nRating, takeAgain, difficulty, status, pId = (
            adapter.validate_python(db_response)
        )
        return Rating(
            prof=prof,
            score=score,
            avg=avg,
            nRating=nRating,
            takeAgain=takeAgain,
            difficulty=difficulty,
            status=status,
            pId=pId,
        )


class LecLab(SQLModel, table=True):
    section_id: int = Field(default=-1, index=True, foreign_key="section.id")
    title: str = Field(default="")
    type: Literal["lecture", "laboratory"] | None = Field(default=None)
    prof: str = Field(default="")
    time: Time = Field(default={})

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

    @classmethod
    def validate_db_response(cls, db_response: Any) -> LecLab:
        adapter = TypeAdapter(
            tuple[int, str, str, Literal["lecture", "laboratory"] | None, str]
        )
        section_id, prof, title, type, time = adapter.validate_python(db_response)

        return LecLab(
            section_id=section_id,
            title=title,
            type=type,
            prof=prof,
            time=TypeAdapter[Time](Time).validate_json(time),
        )


class Section(SQLModel, table=True):
    id: int = Field(default=-1, primary_key=True, index=True)
    course: str = Field(default="")
    section: str = Field(default="")
    domain: str = Field(default="")
    code: str = Field(default="")
    title: str = Field(default="")
    more: str = Field(default="")
    view_data: ViewData = Field(default=[])
    times: list[LecLab] = []

    @classmethod
    def validate_db_response(cls, db_response: Any) -> Section:
        adapter = TypeAdapter(tuple[int, str, str, str, str, str, str, str])

        id, course, section_number, domain, code, title, more, view_data = (
            adapter.validate_python(db_response)
        )

        return Section(
            id=id,
            course=course,
            section=section_number,
            domain=domain,
            code=code,
            title=title,
            more=more,
            view_data=TypeAdapter[ViewData](ViewData).validate_json(view_data),
        )


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

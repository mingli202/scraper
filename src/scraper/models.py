import logging
from typing import Any, Literal, Self, override

from pydantic import BaseModel, ConfigDict, TypeAdapter
from pydantic.alias_generators import to_camel


logger = logging.getLogger(__name__)


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )


Time = dict[str, list[str]]  # day: list["HHMM-HHMM"]


class Rating(ConfiguredBaseModel):
    score: float = 0
    avg: float = 0
    nRating: int = 0
    takeAgain: int = 0
    difficulty: float = 0
    status: Literal["found", "foundn't"] = "foundn't"
    prof: str = ""
    pId: str | None = None

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


class LecLab(ConfiguredBaseModel):
    title: str = ""
    type: Literal["lecture", "laboratory"] | None = None
    prof: str = ""
    time: Time = {}

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
        self.time = Time()

    @classmethod
    def validate_db_response(cls, db_response: Any) -> LecLab:
        adapter = TypeAdapter(
            tuple[int, str, str, Literal["lecture", "laboratory"] | None, str]
        )
        _, prof, title, type, time = adapter.validate_python(db_response)

        return LecLab(
            title=title,
            type=type,
            prof=prof,
            time=TypeAdapter(Time).validate_json(time),
        )


ViewData = list[dict[str, list[int]]]


class Section(ConfiguredBaseModel):
    id: int = 0
    course: str = ""
    section: str = ""
    domain: str = ""
    code: str = ""
    title: str = ""
    times: list[LecLab] = []
    more: str = ""
    view_data: ViewData = []

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
            view_data=TypeAdapter(ViewData).validate_json(view_data),
        )


class ColumnsXs(ConfiguredBaseModel):
    section: int
    disc: int
    course_number: int
    course_title: int
    day: int
    time: int


class Word(ConfiguredBaseModel):
    page_number: int
    text: str
    x0: int
    top: int
    doctop: int

    @override
    def __hash__(self):
        return hash(self.model_dump_json(by_alias=True))

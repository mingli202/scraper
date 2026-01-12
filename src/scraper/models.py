import logging
import unittest
from typing import Any, Literal, Self, override

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError
from pydantic.alias_generators import to_camel, to_snake

logger = logging.getLogger(__name__)


class ConfiguredBasedModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )


Time = dict[str, list[str]]


class Rating(ConfiguredBasedModel):
    score: float = 0
    avg: float = 0
    nRating: int = 0
    takeAgain: int = 0
    difficulty: float = 0
    status: Literal["found", "foundn't"] = "foundn't"
    prof: str = ""
    pId: str | None = None


class LecLab(ConfiguredBasedModel):
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


class Section(ConfiguredBasedModel):
    id: int = 0
    course: str = ""
    section: str = ""
    domain: str = ""
    code: str = ""
    times: list[LecLab] = []
    more: str = ""
    view_data: ViewData = []

    @classmethod
    def validate_db_response(cls, db_response: Any) -> Section:
        adapter = TypeAdapter(tuple[int, str, str, str, str, str, str])

        id, course, section_number, domain, code, more, view_data = (
            adapter.validate_python(db_response)
        )

        return Section(
            id=id,
            course=course,
            section=section_number,
            domain=domain,
            code=code,
            more=more,
            view_data=TypeAdapter(ViewData).validate_json(view_data),
        )


class ColumnsXs(ConfiguredBasedModel):
    section: int
    disc: int
    course_number: int
    course_title: int
    day: int
    time: int


class Word(ConfiguredBasedModel):
    page_number: int
    text: str
    x0: int
    top: int
    doctop: int

    @override
    def __hash__(self):
        return hash(self.model_dump_json(by_alias=True))


class ModelsTest(unittest.TestCase):
    def test_to_camel_case(self):
        self.assertEqual(to_camel("section_columns_x"), "sectionColumnsX")
        self.assertEqual(to_camel("view_data"), "viewData")

    def test_to_snake_case(self):
        self.assertEqual(to_snake("sectionColumnsX"), "section_columns_x")
        self.assertEqual(to_snake("viewData"), "view_data")
        self.assertEqual(to_snake("courseNumber"), "course_number")

    def test_serialization_config_0(self):
        columns_x = ColumnsXs(
            section=0,
            disc=1,
            course_number=2,
            course_title=3,
            day=4,
            time=5,
        )

        serialized = columns_x.model_dump_json(by_alias=True)
        self.assertEqual(
            serialized,
            '{"section":0,"disc":1,"courseNumber":2,"courseTitle":3,"day":4,"time":5}',
        )

        _ = ColumnsXs.model_validate_json(serialized, by_alias=True)

    def test_validation_config_1(self):
        serialized = (
            '{"section":0,"disc":1,"coursenumber":2,"courseTitle":3,"day":4,"time":5}'
        )

        self.assertRaises(
            ValidationError,
            lambda: ColumnsXs.model_validate_json(serialized, by_alias=True),
        )


if __name__ == "__main__":
    _ = unittest.main()

import re
import unittest
from typing import Self

from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel, to_snake


def to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")

    if len(components) == 1:
        return components[0]

    return "".join([components[0]] + [x.title() for x in components[1:]])


def to_snake_case(camel_str: str) -> str:
    print(camel_str)
    components = re.split(r"(?<!^)(?=[A-Z])", camel_str)
    snake_str = "_".join(components).lower()
    print(snake_str)
    return snake_str


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
    status: str = "foundn't"
    prof: str = ""


class LecLab(ConfiguredBasedModel):
    title: str = ""
    prof: str = ""
    time: Time = {}
    rating: Rating | None = None

    def update(self, tmp: Self):
        if tmp.title != "":
            self.title = tmp.title

        if tmp.prof != "":
            self.prof = tmp.prof

        self.update_time(tmp.time)

    def update_time(self, tmp: Time):
        for k, v in tmp.items():
            self.time.setdefault(k, []).extend(v)

    def clear(self):
        self.title = ""
        self.prof = ""
        self.time = Time()


ViewData = list[dict[str, list[int]]]


class Section(ConfiguredBasedModel):
    type: str = ""
    count: int = 0
    section: str = ""
    course: str = ""
    code: str = ""
    lecture: LecLab | None = None
    lab: LecLab | None = None
    more: str = ""
    view_data: ViewData = []


class ColumnsXs(ConfiguredBasedModel):
    section: float
    disc: float
    course_number: float
    course_title: float
    day: float
    time: float


class Word(ConfiguredBasedModel):
    text: str
    x0: float
    x1: float
    top: int
    doctop: float
    bottom: float
    upright: bool
    height: float
    width: float
    direction: str


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

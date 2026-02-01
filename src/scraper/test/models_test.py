import unittest

from pydantic import ValidationError
from pydantic.alias_generators import to_camel, to_snake

from scraper.models import ColumnsXs


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

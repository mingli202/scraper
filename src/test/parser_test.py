import copy
import inspect
import unittest
from typing import Callable

import pytest

from files import Files
from models import LecLab, Section
from parser import Parser


@pytest.mark.skip(reason="deprecated Parser")
class TestParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = Files()
        cls.parser = Parser(cls.files)

    def setUp(self) -> None:
        self.parser.sections = []
        self.parser.currentClass = Section()

    def get_row_data(self, row: str) -> tuple[int, str, list[str]]:
        space = len(row) - len(row.lstrip())
        text = row.strip()
        a = [k for k in row.split(" ") if k != ""]

        return space, text, a

    def t(self, func: Callable) -> tuple[Callable, LecLab]:
        sig = inspect.signature(func)
        tmp = LecLab()

        def f(row: str):
            space, text, a = self.get_row_data(row)
            variable_dict = {
                "space": space,
                "text": text,
                "a": a,
                "row": row,
                "tmp": tmp,
            }
            function_params = {k: variable_dict[k] for k in sig.parameters.keys()}
            func(**function_params)

        return f, tmp

    def test_program_line(self):
        t, _ = self.t(self.parser.parse_program_line)

        for s in [
            "                                                    Science Courses",
            "                                      Social Science / Commerce Courses",
            "                                                  Visual Arts Courses",
            "                                                      Arts & Science",
            "                                        Arts, Literature & Communication",
            "                                                 Liberal Arts Courses",
            "                                                   Pathways Courses",
            "                                                           English",
            "                                                           French",
            "                                                        Humanities",
            "                                                  Physical Education",
            "                                                    Career Programs",
            "                                              Complementary Courses",
        ]:
            t(s)
            self.assertEqual(self.parser.currentClass, Section(program=s.strip()))

        t("this should not work")
        self.assertEqual(
            self.parser.currentClass, Section(program="Complementary Courses")
        )

    def test_course_line(self):
        t, _ = self.t(self.parser.parse_course_line)

        t("ENGLISH")
        self.assertEqual(
            self.parser.currentClass, Section(domain="ENGLISH"), "should set"
        )

        t("HUMANITIES                      ")
        self.assertEqual(
            self.parser.currentClass, Section(domain="HUMANITIES"), "should replace"
        )

        t("asdfoweur023984")
        self.assertEqual(
            self.parser.currentClass, Section(domain="HUMANITIES"), "should not work"
        )

        t("  FRENCH")
        self.assertEqual(
            self.parser.currentClass, Section(domain="HUMANITIES"), "should not work"
        )

    def test_section_line(self):
        t, tmp = self.t(self.parser.parse_section_line)

        self.assertEqual(
            self.parser.currentClass,
            Section(domain="", section="", code="", lecture=None),
        )

        t(
            "00001        HISA        520-AH3-AB            Art History III - Understanding Contemporary Art        W              1300-1600"
        )
        self.parser.updateSection(tmp)
        self.assertEqual(
            self.parser.sections[-1],
            Section(
                domain="",
                section="00001",
                code="520-AH3-AB",
                lecture=LecLab(
                    title="Art History III - Understanding Contemporary Art",
                    time={
                        "W": ["1300-1600"],
                    },
                ),
            ).model_dump(),
            "should have these values",
        )

        t(
            "00001        CRIMINOLOGY    310-518-AB            Fieldwork I - Practical                                 MW             0830-1800"
        )
        self.parser.updateSection(tmp)

        self.assertEqual(
            self.parser.sections[-1],
            Section(
                count=1,
                domain="",
                section="00001",
                code="310-518-AB",
                lecture=LecLab(
                    title="Fieldwork I - Practical",
                    time={
                        "MW": ["0830-1800"],
                    },
                ),
            ).model_dump(),
            "should replace with these new values",
        )

        self.assertEqual(self.parser.sections.__len__(), 2)

    def test_lecture_line(self):
        t, _ = self.t(self.parser.parse_lecture_line)

        t("                         Laboratory            MacLean, Roger")
        self.assertEqual(self.parser.currentClass, Section())

        t("                         Lecture")
        self.assertEqual(self.parser.currentClass, Section(lecture=LecLab(prof="")))

        t("                         Lecture               Dukanic, Filip")
        self.assertEqual(
            self.parser.currentClass, Section(lecture=LecLab(prof="Dukanic, Filip"))
        )

        t(
            "                         Lecture               Lucier, Jason                                           W              1330-1430"
        )
        self.assertEqual(
            self.parser.currentClass,
            Section(lecture=LecLab(prof="Lucier, Jason", time={"W": ["1330-1430"]})),
        )

    def test_lab_line(self):
        t, tmp = self.t(self.parser.parse_lab_line)

        t(
            "             DENT        111-316-AB            Periodontal Instrumentation                             R             0830-1030"
        )
        self.assertEqual(
            tmp,
            LecLab(title="Periodontal Instrumentation", time={"R": ["0830-1030"]}),
        )

    def test_laboratory_line(self):
        t, _ = self.t(self.parser.parse_laboratory_line)

        t("                         Laboratory")
        self.assertEqual(self.parser.currentClass, Section(lab=LecLab(prof="")))

        t("                         Laboratory            MacLean, Roger")
        self.assertEqual(
            self.parser.currentClass, Section(lab=LecLab(prof="MacLean, Roger"))
        )

        t(
            "                         Laboratory            Hasko, Anila                                            F              1030-1230"
        )
        self.assertEqual(
            self.parser.currentClass,
            Section(lab=LecLab(prof="Hasko, Anila", time={"F": ["1030-1230"]})),
        )

    def test_random_floating_time(self):
        t, tmp = self.t(self.parser.parse_random_floating_line)

        t(
            "                                                                                                       R              1600-1800"
        )
        self.assertEqual(tmp, LecLab(time={"R": ["1600-1800"]}))

    def test_implementation_1(self):
        rows = [
            "                                                    Science Courses",
            "BIOLOGY",
            " 101-SN1-AB Co-requisite: 202-SN2-RE or 202-SF2-AB",
            "00001        BIOL        101-SN1-RE            Cellular Biology                                        W              1200-1400",
            "                         Lecture               Daoust, Simon",
            "             BIOL        101-SN1-RE            Cellular Biology                                        T              0830-1030",
            "                         Laboratory            Daoust, Simon",
        ]
        tmp = LecLab()

        for row in rows:
            self.parser.parse_row(row, tmp)

        self.assertEqual(self.parser.sections.__len__(), 0)
        self.assertEqual(
            self.parser.currentClass,
            Section(
                program="Science Courses",
                domain="BIOLOGY",
                count=0,
                section="00001",
                code="101-SN1-RE",
                lecture=LecLab(
                    prof="Daoust, Simon",
                    time={"W": ["1200-1400"]},
                    title="Cellular Biology",
                ),
                lab=LecLab(
                    prof="Daoust, Simon",
                    title="Cellular Biology",
                    time={"T": ["0830-1030"]},
                ),
            ),
            "Basic section parsing",
        )

        first_class = copy.deepcopy(self.parser.currentClass)

        rows = [
            "00005        BIOL        101-SN1-RE            Cellular Biology                                        T              0800-1000",
            "                         Lecture               Parkhill, Jean-Paul",
            "             BIOL        101-SN1-RE            Cellular Biology                                        W              1030-1230",
            "                         Laboratory            Parkhill, Jean-Paul",
        ]

        for row in rows:
            self.parser.parse_row(row, tmp)

        self.assertEqual(
            self.parser.sections.__len__(),
            1,
            "section count should be updated correctly",
        )
        self.assertListEqual(
            self.parser.sections,
            [first_class.model_dump()],
            "section list should be updated when encountering the next section",
        )
        self.assertEqual(
            self.parser.currentClass,
            Section(
                program="Science Courses",
                domain="BIOLOGY",
                count=1,
                section="00005",
                code="101-SN1-RE",
                lecture=LecLab(
                    prof="Parkhill, Jean-Paul",
                    title="Cellular Biology",
                    time={"T": ["0800-1000"]},
                ),
                lab=LecLab(
                    prof="Parkhill, Jean-Paul",
                    time={"W": ["1030-1230"]},
                    title="Cellular Biology",
                ),
            ),
            "Next section should override",
        )

    def test_implementation_2(self):
        rows = [
            "                                                    Science Courses",
            "BIOLOGY",
            " 101-SN1-AB Co-requisite: 202-SN2-RE or 202-SF2-AB",
            "00010        BIOL        101-SN1-RE            Cellular Biology                                        F              1300-1500",
            "                         Lecture               von Roretz, Christopher",
            "                         For Honours Science students only",
            "             BIOL        101-SN1-RE            Cellular Biology                                        R              1030-1230",
            "                         Laboratory            von Roretz, Christopher",
        ]

        tmp = LecLab()

        for row in rows:
            self.parser.parse_row(row, tmp)

        self.assertEqual(self.parser.sections.__len__(), 0)
        self.assertEqual(
            self.parser.currentClass,
            Section(
                program="Science Courses",
                domain="BIOLOGY",
                count=0,
                section="00010",
                code="101-SN1-RE",
                lecture=LecLab(
                    prof="von Roretz, Christopher",
                    title="Cellular Biology",
                    time={"F": ["1300-1500"]},
                ),
                lab=LecLab(
                    prof="von Roretz, Christopher",
                    time={"R": ["1030-1230"]},
                    title="Cellular Biology",
                ),
                more="For Honours Science students only ",
            ),
            "should show more",
        )

        rows = [
            "00012        BIOL        101-SN1-RE            Cellular Biology                                        T              1300-1500",
            "                         Lecture               Hughes, Cameron",
            "             BIOL        101-SN1-RE            Cellular Biology                                        R              1430-1630",
            "                         Laboratory            Hughes, Cameron",
            " 101-NYA-05",
            "00001        BIOL        101-NYA-05            General Biology I                                       TF             1130-1300",
            "                         Lecture               Hughes, Cameron",
            "                         For students in the old science program prior to Fall 2024.",
            "             BIOL        101-NYA-05            General Biology I                                       M              1230-1430",
            "                         Laboratory            Hughes, Cameron",
        ]

        for row in rows:
            self.parser.parse_row(row, tmp)

        self.assertEqual(self.parser.sections.__len__(), 2)
        self.assertEqual(
            self.parser.currentClass,
            Section(
                program="Science Courses",
                domain="BIOLOGY",
                count=2,
                section="00001",
                code="101-NYA-05",
                lecture=LecLab(
                    prof="Hughes, Cameron",
                    time={"TF": ["1130-1300"]},
                    title="General Biology I",
                ),
                lab=LecLab(
                    prof="Hughes, Cameron",
                    time={"M": ["1230-1430"]},
                    title="General Biology I",
                ),
                more="For students in the old science program prior to Fall 2024. ",
            ),
            "change course code",
        )

        rows = [
            "00002        BIOL        101-NYA-05            General Biology I                                       TF             1130-1300",
            "                         Lecture",
            "                         *** Not open, may open during registration ***",
            "                         For students in the old science program prior to Fall 2024.",
            "                                                    Science Courses",
            "BIOLOGY",
            " 101-NYA-05",
            "             BIOL        101-NYA-05            General Biology I                                       M              1430-1630",
            "                         Laboratory",
        ]

        for row in rows:
            self.parser.parse_row(row, tmp)

        self.assertEqual(self.parser.sections.__len__(), 3)
        self.assertEqual(
            self.parser.currentClass,
            Section(
                program="Science Courses",
                domain="BIOLOGY",
                count=3,
                section="00002",
                code="101-NYA-05",
                lecture=LecLab(
                    prof="",
                    time={"TF": ["1130-1300"]},
                    title="General Biology I",
                ),
                lab=LecLab(
                    prof="",
                    time={"M": ["1430-1630"]},
                    title="General Biology I",
                ),
                more="*** Not open, may open during registration ***\nFor students in the old science program prior to Fall 2024. ",
            ),
            "double more line",
        )

    def test_career_programs(self):
        rows = [
            "                                                    Career Programs",
            " 180-51J-C (LECTURE)",
            "00001        NURS        180-51J-C             Nursing V                                               MT             0800-1000",
            "                         Lecture",
        ]

        tmp = LecLab()

        for row in rows:
            self.parser.parse_row(row, tmp)

        self.assertEqual(
            self.parser.currentClass,
            Section(
                program="Career Programs",
                code="180-51J-C",
                lecture=LecLab(
                    title="Nursing V",
                    prof="",
                    time={"MT": ["0800-1000"]},
                ),
                count=0,
                section="00001",
            ),
            "should be equal",
        )

        rows = [
            " 180-10D-L  (LABORATORY)",
            "00011        NURS        180-10D-L             Introduction to Nursing I - Laboratory                  WF            1530-1630",
            "                         Laboratory                                                                    F              1330-1430",
        ]

        for row in rows:
            self.parser.parse_row(row, tmp)

        self.assertEqual(
            self.parser.currentClass,
            Section(
                program="Career Programs",
                code="180-10D-L",
                lab=LecLab(
                    title="Introduction to Nursing I - Laboratory",
                    prof="",
                    time={"WF": ["1530-1630"], "F": ["1330-1430"]},
                ),
                count=1,
                section="00011",
            ),
            "no lecture only lab tf",
        )

    def test_no_lecture_row(self):
        rows = [
            "                                                    Career Programs",
            " 180-10D-LS (CLINICAL)",
            "00021        NURS        180-10D-LS            Introduction to Nursing I - clinical                    W             0830-1130",
            "                                                                                                       W              1200-1400",
            "00022        NURS        180-10D-LS            Introduction to Nursing I - clinical                    W             0830-1130",
            "                                                                                                       W              1200-1400",
        ]

        tmp = LecLab()

        for row in rows:
            self.parser.parse_row(row, tmp)

        self.parser.updateSection(tmp)
        self.assertEqual(
            self.parser.sections,
            [
                Section(
                    program="Career Programs",
                    code="180-10D-LS",
                    section="00021",
                    lecture=LecLab(
                        title="Introduction to Nursing I - clinical",
                        time={"W": ["0830-1130", "1200-1400"]},
                    ),
                ).model_dump(),
                Section(
                    count=1,
                    program="Career Programs",
                    code="180-10D-LS",
                    section="00022",
                    lecture=LecLab(
                        title="Introduction to Nursing I - clinical",
                        time={"W": ["0830-1130", "1200-1400"]},
                    ),
                ).model_dump(),
            ],
        )

    def test_section_edge_case(self):
        section_edge_case = [
            "00001        THEA        561-A5R-AB            Production Lab 3                                        M             1430-1730",
            "                         Lecture               Fauquembergue, Kevin                                    W             1100-1200",
            "                         ADDITIONAL FEE:       $60.00                                                  W             1800-2000",
            "                                                                                                       F              1430-1830",
        ]

        tmp = LecLab()

        for row in section_edge_case:
            self.parser.parse_row(row, tmp)

        self.parser.updateSection(tmp)
        self.assertEqual(
            self.parser.sections[-1],
            Section(
                count=0,
                code="561-A5R-AB",
                lecture=LecLab(
                    title="Production Lab 3",
                    prof="Fauquembergue, Kevin",
                    time={
                        "M": ["1430-1730"],
                        "W": ["1100-1200", "1800-2000"],
                        "F": ["1430-1830"],
                    },
                ),
                section="00001",
            ).model_dump(),
        )

    def test_double_lecture_line(self):
        double_lecture_line = [
            "00001        FILM        530-MTE-AB            Media and the Environment                               W              1200-1430",
            "                         Lecture               Young, Ryan",
            "             FILM        530-MTE-AB            Media and the Environment                               W              1130-1200",
            "                         Lecture               Young, Ryan",
        ]

        tmp = LecLab()
        for row in double_lecture_line:
            self.parser.parse_row(row, tmp)

        self.parser.updateSection(tmp)
        self.assertEqual(
            self.parser.sections[-1],
            Section(
                section="00001",
                code="530-MTE-AB",
                lecture=LecLab(
                    title="Media and the Environment",
                    prof="Young, Ryan",
                    time={"W": ["1200-1430", "1130-1200"]},
                ),
            ).model_dump(),
        )


blended_section_case = [
    "00001        INFO        393-JEB-AB            Information Sources & Services III (Blended)            TR             1330-1530",
    "                         Lecture               Maude, Melissa",
    "                         BLENDED LEARNING. This course will be delivered in blended learning format, involving a percentage of ",
    "                         technology-mediated asynchronous lectures, labs and/or other activities and a percentage in person on ",
    "                         campus lectures. A computer, reliable internet connection, webcam, and microphone are required to ",
    "                         complete your asynchronous activities.",
]

if __name__ == "__main__":
    unittest.main()

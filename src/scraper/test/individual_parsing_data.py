from collections import OrderedDict
from typing import Any
from pydantic import BaseModel

from scraper.files import Files
from scraper.models import DayTime, LecLab, LecLabType, Section, Word
from scraper.new_parser import NewParser


class ATestCase(BaseModel):
    name: str
    lines: OrderedDict[int, list[Word]]


raw_data: list[tuple[dict[str, Any], Section]] = [
    (
        {
            "name": "basic lecture",
            "lines": [
                ["00001", "GERM", "609-DAA-03", "German I", "TR", "1300-1430"],
                ["", "", "Lecture", "Siderova, Spaska", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="609-DAA-03",
            title="German I",
            leclabs=[
                LecLab.default(
                    title="German I",
                    prof="Siderova, Spaska",
                    day_times=[
                        DayTime(
                            day="TR",
                            start_time_hhmm="1300",
                            end_time_hhmm="1430",
                        )
                    ],
                    type=LecLabType.LECTURE,
                )
            ],
        ),
    ),
    (
        {
            "name": "lecture with more",
            "lines": [
                ["00001", "GERM", "609-DAA-03", "German I", "TR", "1300-1430"],
                ["", "", "Lecture", "Siderova, Spaska", "", ""],
                ["", "", "BLENDED LEARNING", "", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="609-DAA-03",
            title="German I",
            leclabs=[
                LecLab.default(
                    title="German I",
                    prof="Siderova, Spaska",
                    day_times=[
                        DayTime(
                            day="TR",
                            start_time_hhmm="1300",
                            end_time_hhmm="1430",
                        )
                    ],
                    type=LecLabType.LECTURE,
                )
            ],
            more="BLENDED LEARNING",
        ),
    ),
    (
        {
            "name": "basic lab",
            "lines": [
                ["00001", "GERM", "609-DAA-03", "German I", "TR", "1300-1430"],
                ["", "", "Laboratory", "Siderova, Spaska", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="609-DAA-03",
            title="German I",
            leclabs=[
                LecLab.default(
                    title="German I",
                    prof="Siderova, Spaska",
                    day_times=[
                        DayTime(
                            day="TR",
                            start_time_hhmm="1300",
                            end_time_hhmm="1430",
                        )
                    ],
                    type=LecLabType.LAB,
                )
            ],
        ),
    ),
    (
        {
            "name": "basic lecture and lab",
            "lines": [
                ["00001", "BIOL", "101-SN1-AB", "Cellular Biology", "R", "0930-1130"],
                ["", "", "Lecture", "Dupont, Sarah", "", ""],
                ["", "BIOL", "101-SN1-AB", "Cellular Biology", "T", "1230-1430"],
                ["", "", "Laboratory", "Hughes, Cameron", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="101-SN1-AB",
            title="Cellular Biology",
            leclabs=[
                LecLab.default(
                    title="Cellular Biology",
                    prof="Dupont, Sarah",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="0930",
                            end_time_hhmm="1130",
                        )
                    ],
                    type=LecLabType.LECTURE,
                ),
                LecLab.default(
                    title="Cellular Biology",
                    prof="Hughes, Cameron",
                    day_times=[
                        DayTime(
                            day="T",
                            start_time_hhmm="1230",
                            end_time_hhmm="1430",
                        )
                    ],
                    type=LecLabType.LAB,
                ),
            ],
        ),
    ),
    (
        {
            "name": "hanging day/times",
            "lines": [
                ["00001", "GERM", "609-DAA-03", "German I", "TR", "1300-1430"],
                ["", "", "Laboratory", "Siderova, Spaska", "M", "0900-1000"],
                ["", "", "", "", "W", "0900-1000"],
            ],
        },
        Section.default(
            section="00001",
            code="609-DAA-03",
            title="German I",
            leclabs=[
                LecLab.default(
                    title="German I",
                    prof="Siderova, Spaska",
                    day_times=[
                        DayTime(
                            day="TR",
                            start_time_hhmm="1300",
                            end_time_hhmm="1430",
                        ),
                        DayTime(
                            day="M",
                            start_time_hhmm="0900",
                            end_time_hhmm="1000",
                        ),
                        DayTime(
                            day="W",
                            start_time_hhmm="0900",
                            end_time_hhmm="1000",
                        ),
                    ],
                    type=LecLabType.LAB,
                )
            ],
        ),
    ),
    (
        {
            "name": "stuck disc",
            "lines": [
                ["00001", "VA &", "511-DBA-03", "Design", "R", "1300-1600"],
                ["", "CERAMICLecture", "", "Lupien, Jennifer", "", ""],
                ["", "", "ADDITIONAL FEE: $80.00", "", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Design",
            leclabs=[
                LecLab.default(
                    title="Design",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1600",
                        )
                    ],
                    type=LecLabType.LECTURE,
                )
            ],
            more="ADDITIONAL FEE: $80.00",
        ),
    ),
    (
        {
            "name": "double line title",
            "lines": [
                [
                    "00001",
                    "VA &",
                    "511-DBA-03",
                    "Art oratoire en public pour des présentations puissantes",
                    "R",
                    "1300-1600",
                ],
                ["", "", "", "et", "", ""],
                ["", "", "Lecture", "Lupien, Jennifer", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Art oratoire en public pour des présentations puissantes et",
            leclabs=[
                LecLab.default(
                    title="Art oratoire en public pour des présentations puissantes et",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1600",
                        )
                    ],
                    type=LecLabType.LECTURE,
                )
            ],
        ),
    ),
    (
        {
            "name": "stuck disc and double line title",
            "lines": [
                ["00001", "VA &", "511-DBA-03", "Design", "R", "1300-1600"],
                ["", "", "", "Design", "", ""],
                ["", "CERAMICLecture", "", "Lupien, Jennifer", "", ""],
                ["", "", "ADDITIONAL FEE: $80.00", "", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Design Design",
            leclabs=[
                LecLab.default(
                    title="Design Design",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1600",
                        )
                    ],
                    type=LecLabType.LECTURE,
                )
            ],
            more="ADDITIONAL FEE: $80.00",
        ),
    ),
    (
        {
            "name": "missing prof",
            "lines": [
                [
                    "00001",
                    "VA &",
                    "511-DBA-03",
                    "Art oratoire en public pour des présentations puissantes",
                    "R",
                    "1300-1600",
                ],
                ["", "", "Lecture", "", "", ""],
                ["", "", "*** Not open. May open during registration. ***", "", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Art oratoire en public pour des présentations puissantes",
            leclabs=[
                LecLab.default(
                    title="Art oratoire en public pour des présentations puissantes",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1600",
                        )
                    ],
                    type=LecLabType.LECTURE,
                )
            ],
            more="*** Not open. May open during registration. ***",
        ),
    ),
    (
        {
            "name": "missing prof and double title line",
            "lines": [
                [
                    "00001",
                    "VA &",
                    "511-DBA-03",
                    "Art oratoire en public pour des présentations puissantes",
                    "R",
                    "1300-1600",
                ],
                ["", "", "", "et", "", ""],
                ["", "", "Lecture", "", "", ""],
                ["", "", "*** Not open. May open during registration. ***", "", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Art oratoire en public pour des présentations puissantes et",
            leclabs=[
                LecLab.default(
                    title="Art oratoire en public pour des présentations puissantes et",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1600",
                        )
                    ],
                    type=LecLabType.LECTURE,
                )
            ],
            more="*** Not open. May open during registration. ***",
        ),
    ),
    (
        {
            "name": "missing 'Lecture' keyword",
            "lines": [
                [
                    "00001",
                    "VA &",
                    "511-DBA-03",
                    "Art oratoire en public pour des présentations puissantes",
                    "R",
                    "1300-1600",
                ],
                ["", "", "", "Lupien, Jennifer", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Art oratoire en public pour des présentations puissantes",
            leclabs=[
                LecLab.default(
                    title="Art oratoire en public pour des présentations puissantes",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1600",
                        )
                    ],
                )
            ],
        ),
    ),
    (
        {
            "name": "missing 'Lecture' keyword and double title line",
            "lines": [
                [
                    "00001",
                    "VA &",
                    "511-DBA-03",
                    "Art oratoire en public pour des présentations puissantes",
                    "R",
                    "1300-1600",
                ],
                ["", "", "", "et", "", ""],
                ["", "", "", "Lupien, Jennifer", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Art oratoire en public pour des présentations puissantes et",
            leclabs=[
                LecLab.default(
                    title="Art oratoire en public pour des présentations puissantes et",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1600",
                        )
                    ],
                )
            ],
        ),
    ),
    (
        {
            "name": "missing 'Lecture' keyword and valid prof name",
            "lines": [
                [
                    "00001",
                    "VA &",
                    "511-DBA-03",
                    "Art oratoire en public pour des présentations puissantes",
                    "R",
                    "1300-1600",
                ],
                ["", "", "", "Lupien, Jennifer", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Art oratoire en public pour des présentations puissantes",
            leclabs=[
                LecLab.default(
                    title="Art oratoire en public pour des présentations puissantes",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1600",
                        )
                    ],
                )
            ],
        ),
    ),
    (
        {
            "name": "missing 'Lecture' keyword and TBA prof name",
            "lines": [
                [
                    "00001",
                    "VA &",
                    "511-DBA-03",
                    "Art oratoire en public pour des présentations puissantes",
                    "R",
                    "1300-1600",
                ],
                ["", "", "", "TBA-1, English", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Art oratoire en public pour des présentations puissantes",
            leclabs=[
                LecLab.default(
                    title="Art oratoire en public pour des présentations puissantes",
                    prof="TBA-1, English",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1600",
                        )
                    ],
                )
            ],
        ),
    ),
    (
        {
            "name": "missing 'Lecture' keyword and invalid prof name",
            "lines": [
                [
                    "00001",
                    "VA &",
                    "511-DBA-03",
                    "Art oratoire en public pour des présentations puissantes",
                    "R",
                    "1300-1600",
                ],
                ["", "", "", "et", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Art oratoire en public pour des présentations puissantes et",
            leclabs=[
                LecLab.default(
                    title="Art oratoire en public pour des présentations puissantes et",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1600",
                        )
                    ],
                )
            ],
        ),
    ),
    (
        {
            "name": "duplicate days",
            "lines": [
                [
                    "00001",
                    "VA &",
                    "511-DBA-03",
                    "Art oratoire en public pour des présentations puissantes",
                    "R",
                    "1300-1500",
                ],
                ["", "", "Lecture", "Lupien, Jennifer", "R", "1500-1600"],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Art oratoire en public pour des présentations puissantes",
            leclabs=[
                LecLab.default(
                    title="Art oratoire en public pour des présentations puissantes",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1500",
                        ),
                        DayTime(
                            day="R",
                            start_time_hhmm="1500",
                            end_time_hhmm="1600",
                        ),
                    ],
                    type=LecLabType.LECTURE,
                )
            ],
        ),
    ),
    (
        {
            "name": "double lecture",
            "lines": [
                ["00001", "VA &", "511-DBA-03", "Design", "R", "1300-1500"],
                ["", "", "Lecture", "Lupien, Jennifer", "", ""],
                ["", "VA &", "511-DBA-03", "Design", "R", "1500-1600"],
                ["", "", "Lecture", "Lupien, Jennifer", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Design",
            leclabs=[
                LecLab.default(
                    title="Design",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1500",
                        )
                    ],
                    type=LecLabType.LECTURE,
                ),
                LecLab.default(
                    title="Design",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1500",
                            end_time_hhmm="1600",
                        )
                    ],
                    type=LecLabType.LECTURE,
                ),
            ],
        ),
    ),
    (
        {
            "name": "triple lecture",
            "lines": [
                ["00001", "VA &", "511-DBA-03", "Design", "R", "1300-1500"],
                ["", "", "Lecture", "Lupien, Jennifer", "", ""],
                ["", "VA &", "511-DBA-03", "Design", "R", "1500-1600"],
                ["", "", "Lecture", "Lupien, Jennifer", "", ""],
                ["", "VA &", "511-DBA-03", "Design", "R", "1600-1700"],
                ["", "", "Lecture", "Lupien, Jennifer", "", ""],
            ],
        },
        Section.default(
            section="00001",
            code="511-DBA-03",
            title="Design",
            leclabs=[
                LecLab.default(
                    title="Design",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1300",
                            end_time_hhmm="1500",
                        )
                    ],
                    type=LecLabType.LECTURE,
                ),
                LecLab.default(
                    title="Design",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1500",
                            end_time_hhmm="1600",
                        )
                    ],
                    type=LecLabType.LECTURE,
                ),
                LecLab.default(
                    title="Design",
                    prof="Lupien, Jennifer",
                    day_times=[
                        DayTime(
                            day="R",
                            start_time_hhmm="1600",
                            end_time_hhmm="1700",
                        )
                    ],
                    type=LecLabType.LECTURE,
                ),
            ],
        ),
    ),
]


files = Files()
parser = NewParser(files)

xs = [
    parser.columns_x.section,
    parser.columns_x.disc,
    parser.columns_x.course_number,
    parser.columns_x.course_title,
    parser.columns_x.day,
    parser.columns_x.time,
]


def func(x: dict[str, Any]) -> ATestCase:
    lines: OrderedDict[int, list[Word]] = OrderedDict()

    lines.update({-2: [Word(page_number=0, text="title line", x0=0, top=0, doctop=0)]})
    lines.update({-1: [Word(page_number=0, text="", x0=0, top=0, doctop=0)]})

    for i, line in enumerate(x["lines"]):
        new_line: list[Word] = []

        for k, word in enumerate(line):
            assert isinstance(word, str)

            if word == "":
                continue

            word = Word(page_number=0, text=word, x0=xs[k], top=0, doctop=0)
            new_line.append(word)

        lines.update({i: new_line})

    return ATestCase(name=x["name"], lines=lines)


data: list[tuple[ATestCase, Section]] = [(func(test), exp) for test, exp in raw_data]

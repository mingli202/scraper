from collections import OrderedDict
from typing import Any
from pydantic import BaseModel

from files import Files
from models import LecLab, Section, Word
from new_parser import NewParser


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
        Section(
            section="00001",
            code="609-DAA-03",
            times=[
                LecLab(
                    title="German I",
                    prof="Siderova, Spaska",
                    time={"TR": ["1300-1430"]},
                    type="lecture",
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
        Section(
            section="00001",
            code="609-DAA-03",
            times=[
                LecLab(
                    title="German I",
                    prof="Siderova, Spaska",
                    time={"TR": ["1300-1430"]},
                    type="lecture",
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
        Section(
            section="00001",
            code="609-DAA-03",
            times=[
                LecLab(
                    title="German I",
                    prof="Siderova, Spaska",
                    time={"TR": ["1300-1430"]},
                    type="laboratory",
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
        Section(
            section="00001",
            code="101-SN1-AB",
            times=[
                LecLab(
                    title="Cellular Biology",
                    prof="Dupont, Sarah",
                    time={"R": ["0930-1130"]},
                    type="lecture",
                ),
                LecLab(
                    title="Cellular Biology",
                    prof="Hughes, Cameron",
                    time={"T": ["1230-1430"]},
                    type="laboratory",
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
        Section(
            section="00001",
            code="609-DAA-03",
            times=[
                LecLab(
                    title="German I",
                    prof="Siderova, Spaska",
                    time={"TR": ["1300-1430"], "M": ["0900-1000"], "W": ["0900-1000"]},
                    type="laboratory",
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
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Design",
                    prof="Lupien, Jennifer",
                    time={"R": ["1300-1600"]},
                    type="lecture",
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
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Art oratoire en public pour des présentations puissantes et",
                    prof="Lupien, Jennifer",
                    time={"R": ["1300-1600"]},
                    type="lecture",
                )
            ],
            more="ADDITIONAL FEE: $80.00",
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
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Design Design",
                    prof="Lupien, Jennifer",
                    time={"R": ["1300-1600"]},
                    type="lecture",
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
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Art oratoire en public pour des présentations puissantes",
                    time={"R": ["1300-1600"]},
                    type="lecture",
                )
            ],
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
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Art oratoire en public pour des présentations puissantes et",
                    time={"R": ["1300-1600"]},
                    type="lecture",
                )
            ],
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
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Art oratoire en public pour des présentations puissantes",
                    prof="Lupien, Jennifer",
                    time={"R": ["1300-1600"]},
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
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Art oratoire en public pour des présentations puissantes et",
                    prof="Lupien, Jennifer",
                    time={"R": ["1300-1600"]},
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
                ["", "", "", "Lupien, Jennifer", "R", "1500-1600"],
            ],
        },
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Art oratoire en public pour des présentations puissantes",
                    prof="Lupien, Jennifer",
                    time={"R": ["1300-1500", "1500-1600"]},
                    type="lecture",
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
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Design",
                    prof="Lupien, Jennifer",
                    time={"R": ["1300-1500", "1500-1600"]},
                    type="lecture",
                )
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
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Design",
                    prof="Lupien, Jennifer",
                    time={"R": ["1300-1500", "1500-1600", "1600-1700"]},
                    type="lecture",
                )
            ],
        ),
    ),
    (
        {
            "name": "overlapping times",
            "lines": [
                ["00001", "VA &", "511-DBA-03", "Design", "R", "1300-1500"],
                ["", "", "Lecture", "Lupien, Jennifer", "R", "1400-1600"],
            ],
        },
        Section(
            section="00001",
            code="511-DBA-03",
            times=[
                LecLab(
                    title="Design",
                    prof="Lupien, Jennifer",
                    time={"R": ["1300-1600"]},
                    type="lecture",
                )
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

    lines.update({-1: [Word(page_number=0, text="title line", x0=0, top=0, doctop=0)]})

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

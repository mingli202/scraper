import os

from pydantic_core import from_json

from models import Rating, Section


class Files:
    def __init__(self, bak: bool = False) -> None:
        semester = "winter"
        if bak:
            semester = semester + ".bak"
        curPath = os.path.dirname(__file__)
        curPath = "/".join(curPath.split("/")[:-1]) + "/"
        semesterDir = curPath + semester + "/" + semester

        self.pdfName = curPath + "SCHEDULE_OF_CLASSES_Winter_2026_December_11.txt"
        self.rawFile = semesterDir + "-raw.json"
        self.classesFile = semesterDir + "-classes.json"
        self.outFile = semesterDir + "-out.json"
        self.organized = semesterDir + "-organized.json"
        self.professors = semesterDir + "-professors.json"
        self.ratings = semesterDir + "-ratings.json"
        self.pids = semesterDir + "-pids.json"
        self.missingPids = semesterDir + "-missing-pid.json"
        self.allClasses = "/".join(semesterDir.split("/")[:-1] + ["allClasses.json"])

    def get_raw_file_content(self) -> list[str]:
        with open(self.rawFile, "r") as file:
            return from_json(file.read())

    def get_ratings_file_content(self) -> dict[str, Rating]:
        with open(self.ratings, "r") as file:
            return {
                k: Rating.model_validate(v) for k, v in from_json(file.read()).items()
            }

    def get_missing_pids_file_content(self) -> dict[str, str]:
        with open(self.missingPids, "r") as file:
            return from_json(file.read())

    def get_professors_file_content(self) -> list[str]:
        with open(self.professors, "r") as file:
            return from_json(file.read())

    def get_pids_file_content(self) -> dict[str, str]:
        with open(self.pids, "r") as file:
            return from_json(file.read())

    def get_out_file_content(self) -> list[Section]:
        with open(self.outFile, "r") as file:
            return [Section.model_validate(s) for s in from_json(file.read())]

    def get_classes_file_content(self) -> list[Section]:
        with open(self.classesFile, "r") as file:
            return [Section.model_validate(s) for s in from_json(file.read())]

    def get_all_classes_file_content(self) -> dict[int, Section]:
        with open(self.allClasses, "r") as file:
            return {
                k: Section.model_validate(v) for k, v in from_json(file.read()).items()
            }

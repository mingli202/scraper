from typing import Self
from pydantic import BaseModel


Time = dict[str, list[str]]


class Rating(BaseModel):
    score: float = 0
    avg: float = 0
    nRating: int = 0
    takeAgain: int = 0
    difficulty: float = 0
    status: str = "foundn't"
    prof: str = ""


class LecLab(BaseModel):
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


class Section(BaseModel):
    program: str = ""
    count: int = 0
    section: str = ""
    course: str = ""
    code: str = ""
    lecture: LecLab | None = None
    lab: LecLab | None = None
    more: str = ""
    viewData: ViewData = []


class ColumnsXs(BaseModel):
    section: float = 0
    disc: float = 0
    course_number: float = 0
    course_title: float = 0
    day_times: float = 0

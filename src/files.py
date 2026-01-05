from collections import OrderedDict
import json
from functools import cache
from pathlib import Path
from typing import Any, final

from pydantic import TypeAdapter, ValidationError
from pydantic_core import from_json

from models import ColumnsXs, Rating, Section, Word
from parser_utils import ParserUtils


@final
class Files:
    def __init__(self, pdf_path: Path | None = None) -> None:
        pwd = Path(__file__).parent.parent.resolve()

        if pdf_path is not None:
            self.pdf_path = pdf_path
        else:
            self.pdf_path = Path(
                "/Users/vincentliu/Downloads/SCHEDULE_OF_CLASSES_Winter_2026_December_11.pdf"
            )

        data_dir = pwd / "data" / self.pdf_path.stem
        data_dir.mkdir(exist_ok=True, parents=True)

        self.sorted_lines_path = data_dir / "sorted_lines.json"
        self.section_columns_x_path = data_dir / "section_columns_x.json"
        self.ratings_path = data_dir / "ratings.json"
        self.missing_pids_path = data_dir / "missingPids.json"
        self.professors_path = data_dir / "professors.json"
        self.pids_path = data_dir / "pids.json"
        self.out_file_path = data_dir / "out.json"
        self.classes_file_path = data_dir / "classes.json"
        self.all_classes_path = data_dir / "allClasses.json"

    @cache
    def get_sorted_lines_content(self) -> OrderedDict[float, list[Word]]:
        if self.sorted_lines_path.exists():
            with open(self.sorted_lines_path, "r") as f:
                try:
                    adapter = TypeAdapter(OrderedDict[float, list[Word]])
                    data = adapter.validate_json(f.read(), by_alias=True)
                    return data
                except ValidationError as e:
                    print(e)

        lines: OrderedDict[float, list[Word]] = ParserUtils.compute_sorted_lines(
            self.pdf_path
        )

        serializable_lines: OrderedDict[float, list[dict[str, Any]]] = OrderedDict()
        for k, v in lines.items():
            serializable_lines[k] = [w.model_dump(by_alias=True) for w in v]

        with open(self.sorted_lines_path, "w") as f:
            json.dump(serializable_lines, f, indent=2)

        return lines

    @cache
    def get_section_columns_x_content(self) -> ColumnsXs:
        if self.section_columns_x_path.exists():
            with open(self.section_columns_x_path, "r") as f:
                try:
                    data = ColumnsXs.model_validate_json(f.read(), by_alias=True)
                    return data
                except ValidationError as e:
                    print(e)

        columns_x: ColumnsXs = ParserUtils.compute_columns_x(
            self.get_sorted_lines_content()
        )

        with open(self.section_columns_x_path, "w") as f:
            json.dump(columns_x.model_dump(by_alias=True), f)

        return columns_x

    def get_ratings_file_content(self) -> dict[str, Rating]:
        with open(self.ratings_path, "r") as file:
            return {
                k: Rating.model_validate(v) for k, v in from_json(file.read()).items()
            }

    def get_missing_pids_file_content(self) -> dict[str, str]:
        with open(self.missing_pids_path, "r") as file:
            return from_json(file.read())

    def get_professors_file_content(self) -> list[str]:
        with open(self.professors_path, "r") as file:
            return from_json(file.read())

    def get_pids_file_content(self) -> dict[str, str]:
        with open(self.pids_path, "r") as file:
            return from_json(file.read())

    def get_out_file_content(self) -> list[Section]:
        with open(self.out_file_path, "r") as file:
            return [
                Section.model_validate(s, by_alias=True) for s in from_json(file.read())
            ]

    def get_classes_file_content(self) -> list[Section]:
        with open(self.classes_file_path, "r") as file:
            return [
                Section.model_validate(s, by_alias=True) for s in from_json(file.read())
            ]

    def get_all_classes_file_content(self) -> dict[int, Section]:
        with open(self.all_classes_path, "r") as file:
            return {
                k: Section.model_validate(v, by_alias=True)
                for k, v in from_json(file.read()).items()
            }

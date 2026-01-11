from collections import OrderedDict
import itertools
import json
from pathlib import Path
from typing import Any, final

from pydantic import TypeAdapter, ValidationError
from pydantic_core import from_json

from models import ColumnsXs, Rating, Section, Word
import parser_utils
from trie import Trie


@final
class Files:
    def __init__(self, pdf_path: Path | None = None) -> None:
        cwd = Path(__file__).parent.parent.resolve()
        self.cwd = cwd

        if pdf_path is not None:
            self.pdf_path = pdf_path
        else:
            self.pdf_path = Path(
                "/Users/vincentliu/Downloads/SCHEDULE_OF_CLASSES_Winter_2026_December_11.pdf"
            )

        data_dir = cwd / "data" / self.pdf_path.stem
        data_dir.mkdir(exist_ok=True, parents=True)

        self.data_dir = data_dir

        self.sorted_lines_path = data_dir / "sorted_lines.json"
        self.section_columns_x_path = data_dir / "section_columns_x.json"
        self.parsed_sections = data_dir / "parsed_sections.json"
        self.ratings_path = data_dir / "ratings.json"
        self.pids_path = cwd / "data" / "pids.json"
        self.professors_path = data_dir / "professors.json"

        self.missing_pids_path = data_dir / "missingPids.json"
        self.classes_file_path = data_dir / "classes.json"
        self.all_classes_path = data_dir / "allClasses.json"

        self.raw_file = cwd / "winter" / "winter-raw.json"
        self.pdf_name = cwd / "SCHEDULE_OF_CLASSES_Winter_2026_December_11.txt"
        self.out_file_path = cwd / "winter" / "winter-out.json"

    def get_sorted_lines_content(
        self, use_cache: bool = True
    ) -> OrderedDict[int, list[Word]]:
        if self.sorted_lines_path.exists() and use_cache:
            with open(self.sorted_lines_path, "r") as f:
                try:
                    adapter = TypeAdapter(OrderedDict[int, list[Word]])
                    data = adapter.validate_json(f.read(), by_alias=True)
                    return data
                except ValidationError as e:
                    print(e)

        lines: OrderedDict[int, list[Word]] = parser_utils.compute_sorted_lines(
            self.pdf_path
        )

        def map(word: Word) -> dict[str, Any]:
            return word.model_dump(by_alias=True)

        serializable_lines: OrderedDict[float, list[dict[str, Any]]] = OrderedDict()
        for k, v in lines.items():
            serializable_lines[k] = [map(w) for w in v]

        with open(self.sorted_lines_path, "w") as f:
            json.dump(serializable_lines, f, indent=2)

        return lines

    def get_section_columns_x_content(self, use_cache: bool = True) -> ColumnsXs:
        if self.section_columns_x_path.exists() and use_cache:
            with open(self.section_columns_x_path, "r") as f:
                try:
                    data = ColumnsXs.model_validate_json(f.read(), by_alias=True)
                    return data
                except ValidationError as e:
                    print(e)

        columns_x: ColumnsXs = parser_utils.compute_columns_x(
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

    def get_parsed_sections_file_content(self) -> list[Section]:
        if not self.parsed_sections.exists():
            return []

        with open(self.parsed_sections, "r") as file:
            return [
                Section.model_validate(s, by_alias=True) for s in from_json(file.read())
            ]

    def get_professors_file_content(self) -> Trie:
        if self.professors_path.exists():
            with open(self.professors_path, "r") as file:
                return Trie.model_validate(from_json(file.read()))

        professors = itertools.chain.from_iterable(
            [t.prof for t in section.times if t.prof != ""]
            for section in self.get_parsed_sections_file_content()
        )

        trie = Trie()

        for prof in professors:
            trie.add(prof)

        with open(self.professors_path, "w") as file:
            _ = file.write(json.dumps(trie.model_dump(by_alias=True), indent=2))

        return trie

    def get_missing_pids_file_content(self) -> dict[str, str]:
        with open(self.missing_pids_path, "r") as file:
            return from_json(file.read())

    def get_pids_file_content(self) -> dict[str, str]:
        with open(self.pids_path, "r") as file:
            return from_json(file.read())

    def get_out_file_content(self) -> list[Section]:
        with open(self.parsed_sections, "r") as file:
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

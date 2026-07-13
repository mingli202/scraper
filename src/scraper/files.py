from collections import OrderedDict
import json
from pathlib import Path
from typing import Any, final

from pydantic import TypeAdapter
from pydantic_core import from_json

from scraper.models import ColumnsXs, GlobalAllSections, Section, Word


@final
class Files:
    def __init__(self, pdf_path: Path | None = None) -> None:
        cwd = Path(__file__).parent.parent.parent.resolve()
        self.cwd = cwd

        if pdf_path is not None:
            self.pdf_path = pdf_path
        else:
            self.pdf_path = cwd / "RPHOR200_-_Schedule_of_classes_June_5.pdf"

        data_dir = cwd / "data"
        semester_data_dir = data_dir / self.pdf_path.stem
        semester_data_dir.mkdir(exist_ok=True, parents=True)

        self.data_dir = semester_data_dir

        self.sorted_lines_path = semester_data_dir / "sorted_lines.json"
        self.columns_x_path = semester_data_dir / "section_columns_x.json"
        self.parsed_sections_path = semester_data_dir / "parsed_sections.json"
        self.pids_path = data_dir / "pids.json"
        self.professors_path = semester_data_dir / "professors.json"
        self.all_sections_final_path_json = (
            semester_data_dir / "all_sections_final.json"
        )
        self.ratings_path = data_dir / "ratings.json"

        self.missing_pids_path = semester_data_dir / "missingPids.json"
        self.global_all_sections_final_path_json = cwd / "all_sections_final.json"

        self.out_file_path = cwd / "winter" / "winter-out.json"  # backwards

    def get_sorted_lines_content(self) -> OrderedDict[int, list[Word]] | None:
        """
        Gets the content of the sorted lines file.
        Returns None if file doesn't exists
        """
        if not self.sorted_lines_path.exists():
            return None

        with open(self.sorted_lines_path, "r") as f:
            adapter = TypeAdapter(OrderedDict[int, list[Word]])
            data = adapter.validate_json(f.read(), by_alias=True)
            return data

    def write_to_sorted_lines(self, lines: OrderedDict[int, list[Word]]) -> None:
        """
        Write the given lines to the sorted lines file
        """

        # lines: OrderedDict[int, list[Word]] = parser_utils.compute_sorted_lines(
        #     self.pdf_path
        # )
        #
        def map(word: Word) -> dict[str, Any]:
            return word.model_dump(by_alias=True)

        serializable_lines: OrderedDict[float, list[dict[str, Any]]] = OrderedDict()
        for k, v in lines.items():
            serializable_lines[k] = [map(w) for w in v]

        with open(self.sorted_lines_path, "w") as f:
            json.dump(serializable_lines, f, indent=2)

    def get_section_columns_x_content(self) -> ColumnsXs:
        """
        Gets the content of the columns_x file
        Raise if file doesn't exist
        """

        with open(self.columns_x_path, "r") as f:
            data = ColumnsXs.model_validate_json(f.read(), by_alias=True)
            return data

    def write_to_columns_x(self, columns_x: ColumnsXs) -> None:
        """
        Write to the columns_x file
        """
        with open(self.columns_x_path, "w") as f:
            json.dump(columns_x.model_dump(by_alias=True), f)

    def get_parsed_sections_file_content(self) -> list[Section]:
        with open(self.parsed_sections_path, "r") as file:
            return [Section.model_validate(s) for s in from_json(file.read())]

    def get_all_sections_final_path_json_content(self) -> dict[str, Section]:
        with open(self.all_sections_final_path_json, "r") as file:
            sections = TypeAdapter(dict[str, Section]).validate_json(file.read())

            return sections

    def get_global_all_sections_content(self) -> GlobalAllSections:
        with open(self.global_all_sections_final_path_json, "r") as file:
            return GlobalAllSections.model_validate_json(file.read())

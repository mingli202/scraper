import json
from functools import cache
from pathlib import Path
from typing import Any, final

from pydantic import TypeAdapter

from models import ColumnsXs
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

    @cache
    def get_sorted_lines_content(self) -> list[list[dict[str, Any]]]:
        if self.sorted_lines_path.exists():
            with open(self.sorted_lines_path, "r") as f:
                adapter = TypeAdapter(list[list[dict[str, Any]]])
                return adapter.validate_json(f.read())

        lines: list[list[dict[str, Any]]] = ParserUtils.compute_sorted_lines(
            self.pdf_path
        )

        with open(self.sorted_lines_path, "w") as f:
            json.dump(lines, f)

        return lines

    @cache
    def get_section_columns_x_content(self) -> ColumnsXs:
        if self.section_columns_x_path.exists():
            with open(self.section_columns_x_path, "r") as f:
                return ColumnsXs.model_validate_json(f.read())

        columns_x: ColumnsXs = ParserUtils.compute_columns_x(
            self.get_sorted_lines_content()
        )

        with open(self.section_columns_x_path, "w") as f:
            json.dump(columns_x.model_dump(), f)

        return columns_x

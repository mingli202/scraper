from pathlib import Path
from typing import final

from pydantic_core import from_json

from models import Rating, Section


@final
class Files:
    def __init__(self) -> None:
        pwd = Path(__file__).parent.parent.resolve()

        self.pdf_path = Path(
            "/Users/vincentliu/Downloads/SCHEDULE_OF_CLASSES_Winter_2026_December_11.pdf"
        )

        data_dir = pwd / "data" / self.pdf_path.stem
        data_dir.mkdir(exist_ok=True, parents=True)

        self.sorted_lines_path = data_dir / "sorted_lines.json"
        self.section_columns_x_path = data_dir / "section_columns_x.json"

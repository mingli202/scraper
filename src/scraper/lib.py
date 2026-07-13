import datetime
import logging
from pathlib import Path

from scraper import new_parser, parser_utils, util
from scraper.models import GlobalAllSections, Rating


def get_current_semester() -> str:
    """
    Gets the current semester at the time this function got called
    """

    now = datetime.datetime.now()

    if 6 <= now.month < 12:
        return f"FALL {now.year}"
    elif now.month == 12:
        return f"WINTER {now.year + 1}"
    elif 1 <= now.month < 6:
        return f"WINTER {now.year}"
    else:
        return f"SUMMER {now.year}"


def the_entire_loop(
    pdf_path: Path,
    ratings: dict[str, Rating],
    max_pages: int | None = None,
) -> GlobalAllSections:
    """The entire loop with no cached sections, no diff and precomputed ratings"""

    semester = get_current_semester()

    logging.log(logging.DEBUG, f"parsing pdf at {pdf_path}")

    parser = new_parser.NewParser()
    sorted_lines, columns_x = parser_utils.get_parser_deps(
        pdf_path, max_pages=max_pages
    )
    sections = parser.parse(sorted_lines, columns_x)

    util.add_rating_to_sections(sections, ratings)
    sections_by_id = util.to_sections_by_id(sections)

    parsed_semester = new_parser.get_semester(sorted_lines)

    if parsed_semester != semester:
        logging.log(
            logging.WARN,
            f"Parsed and current semester differs: parsed {parsed_semester}, current {semester}",
        )

    return GlobalAllSections(
        semester=semester,
        sections_by_id=sections_by_id,
        filename=pdf_path.name,
        sections_diff=None,
        comments=[],
    )

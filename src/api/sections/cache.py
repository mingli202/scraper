from __future__ import annotations

import os
from dataclasses import dataclass

from scraper.files import Files
from scraper.models import Section


@dataclass(frozen=True)
class SectionCache:
    by_id: dict[str, Section]
    all_sections: tuple[Section, ...]


def section_cache_enabled() -> bool:
    return os.environ.get("ENABLE_SECTION_CACHE", "1") != "0"


def load_section_cache() -> SectionCache | None:
    if not section_cache_enabled():
        return None

    files = Files()
    global_sections = files.get_global_all_sections_content()
    all_sections = tuple(
        section.model_copy(update={"id": f"{section.code}-{section.section}"})
        for section in global_sections.sections_by_id.values()
    )
    by_id = {section.id: section for section in all_sections}
    return SectionCache(by_id=by_id, all_sections=all_sections)

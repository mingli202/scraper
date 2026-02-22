from __future__ import annotations

import os
from dataclasses import dataclass

from sqlmodel import Session, select

from api.sections.queries import with_section_relationships
from scraper.db import engine
from scraper.models import Section, SectionResponse


@dataclass(frozen=True)
class SectionCache:
    by_id: dict[int, SectionResponse]
    all_sections: tuple[SectionResponse, ...]


def section_cache_enabled() -> bool:
    return os.environ.get("ENABLE_SECTION_CACHE", "1") != "0"


def load_section_cache() -> SectionCache | None:
    if not section_cache_enabled():
        return None

    with Session(engine) as session:
        statement = with_section_relationships(select(Section))
        sections = session.exec(statement).all()

    all_sections = tuple(
        SectionResponse.model_validate(section) for section in sections
    )
    by_id = {section.id: section for section in all_sections}
    return SectionCache(by_id=by_id, all_sections=all_sections)

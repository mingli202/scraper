from __future__ import annotations

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.sql.expression import SelectOfScalar

from scraper.models import LecLab, Section


def with_section_relationships(statement: SelectOfScalar[Section]):
    return statement.options(
        selectinload(Section.leclabs).selectinload(LecLab.rating),
        selectinload(Section.leclabs).selectinload(LecLab.day_times),
    )


def section_by_id_statement(section_id: int):
    return with_section_relationships(select(Section)).where(Section.id == section_id)

import json
from pathlib import Path


from scraper.files import Files
from scraper.models import (
    GlobalAllSections,
    Rating,
    SectionsDiff,
    Section,
)


def normalize_string(s: str):
    s = s.replace("\u00e9", "e").replace("é", "e")  #  removes é
    s = s.replace("\u00c9", "E").replace("É", "E")  #  removes É
    s = s.replace("\u00e8", "e").replace("è", "e")  #  removes è
    s = s.replace("\u00e2", "a").replace("â", "a")  #  removes â
    s = s.replace("\u00e7", "c").replace("ç", "c")  #  removes ç
    s = s.replace("\u00e0", "a").replace("à", "a")  #  removes à
    s = s.replace("\u0000", "")  #  removes null character

    return s


def make_sections_final(
    sections: list[Section], ratings_by_prof: dict[str, Rating], files: Files
) -> dict[str, Section]:
    """
    Adds teacher ratings to each section
    Writes to the final json {sectionId: Section}
    """

    for section in sections:
        for leclab in section.leclabs:
            leclab.rating = ratings_by_prof.get(leclab.prof)

    sections_dict_json = {
        section.id: section.model_dump(mode="json", by_alias=True)
        for section in sections
    }

    with open(files.all_sections_final_path_json, "w") as file:
        json.dump(
            sections_dict_json,
            file,
            indent=2,
        )

    return {section.id: section for section in sections}


def get_global_sections_diff(
    current_semester: str,
    old_global_all_sections: GlobalAllSections,
    sections_by_id: dict[str, Section],
) -> SectionsDiff | None:
    """
    Gets the difference between the old sections and the incoming sections.
    Checks for added/removed/changed sections.
    For changed sections, every key is compared for equality except for leclab.rating
    since ratings are prone to change frequently but will be small changes, so we don't care
    """

    if old_global_all_sections.semester != current_semester:
        return None

    return get_sections_diff(old_global_all_sections.sections_by_id, sections_by_id)


def get_sections_diff(
    old_sections_by_id: dict[str, Section], new_sections_by_id: dict[str, Section]
) -> SectionsDiff:
    """
    Gets the diff between the old and new sections_by_id
    """

    sections_added: list[str] = []
    sections_removed: list[Section] = []
    previous_sections: list[Section] = []

    for id, old_section in old_sections_by_id.items():
        if id not in new_sections_by_id:
            sections_removed.append(old_section)

        elif is_different(old_section, new_sections_by_id[id]):
            previous_sections.append(old_section)

    for id in new_sections_by_id.keys():
        if id not in old_sections_by_id:
            sections_added.append(id)

    return SectionsDiff(
        previous_sections_changed=previous_sections,
        sections_added=sections_added,
        sections_removed=sections_removed,
    )


def is_different(old_section: Section, new_section: Section) -> bool:
    """
    Checks whether the given old and new sections are the same after removing
    the teacher's rating
    """

    old_section_copy = old_section.model_copy(deep=True)
    new_section_copy = new_section.model_copy(deep=True)

    for leclab in old_section_copy.leclabs:
        leclab.rating = None

    for leclab in new_section_copy.leclabs:
        leclab.rating = None

    return old_section_copy != new_section_copy


def make_global_sections_final(
    semester: str,
    section_by_id: dict[str, Section],
    files: Files,
    diff: SectionsDiff | None,
    comments: list[str],
) -> GlobalAllSections:
    """
    Write to the same place rather than by directory
    """

    filename = files.pdf_path.name
    global_sections = GlobalAllSections(
        semester=semester,
        sections_by_id=dict(sorted(section_by_id.items())),
        filename=filename,
        sections_diff=diff,
        comments=comments,
    )

    with open(files.global_all_sections_final_path_json, "w") as file:
        json.dump(
            global_sections.model_dump(mode="json", by_alias=True), file, indent=2
        )

    return global_sections


def should_override(override: bool | None, path: Path, message: str) -> str | None:
    """
    Whether should override or not the given path, returning the data if
    no override and data exists at the given path
    Ask with the given message if confirmation is needed
    """
    if override is not None:
        return None

    return override_for_path(path, message)


def override_for_path(path: Path, message: str) -> str | None:
    """
    If override is None, ask the user if they want to override or not
    the data at the given path with the given message if there is data.
    Returns the existing data if no override and exists
    Any input other than y/Y is treated as false.
    """

    if path.exists():
        override = input(f"{message} Override? [y]")
        if override.lower() != "y":
            with open(path, "r") as f:
                return f.read()

    return None


def get_professors_from_sections(parsed_sections: list[Section]) -> list[str]:
    """
    Get the list if unique professors from the parsed sections
    """
    profs: set[str] = set()

    for section in parsed_sections:
        profs.update(get_professors_from_section(section))

    return list(profs)


def get_professors_from_section(section: Section) -> list[str]:
    """
    Gets the list of profs for the given section
    """
    return [leclab.prof for leclab in section.leclabs]

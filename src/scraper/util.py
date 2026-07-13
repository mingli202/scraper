from collections import OrderedDict
import json
from pathlib import Path

from pydantic import TypeAdapter


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


def add_rating_to_sections(sections: list[Section], ratings_by_prof: dict[str, Rating]):
    """
    For each of the given sections, adds the approprate rating to the section's leclabs
    """
    for section in sections:
        for leclab in section.leclabs:
            leclab.rating = ratings_by_prof.get(leclab.prof)


def make_sections_final(
    sections: list[Section],
    ratings_by_prof: dict[str, Rating],
    all_sections_final_path_json: Path,
):
    """
    Adds teacher ratings to each section
    Writes to the final json {sectionId: Section}
    """

    add_rating_to_sections(sections, ratings_by_prof)

    sections_dict_json = {
        section.id: section.model_dump(mode="json", by_alias=True)
        for section in sections
    }

    with open(all_sections_final_path_json, "w") as file:
        json.dump(
            sections_dict_json,
            file,
            indent=2,
        )


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


def save_global_sections_final(
    semester: str,
    section_by_id: dict[str, Section],
    pdf_path: Path,
    global_all_sections_final_path_json: Path,
    diff: SectionsDiff | None,
    comments: list[str],
) -> GlobalAllSections:
    """
    Write to the same place rather than by directory
    """

    filename = pdf_path.name
    global_sections = GlobalAllSections(
        semester=semester,
        sections_by_id=OrderedDict(sorted(section_by_id.items())),
        filename=filename,
        sections_diff=diff,
        comments=comments,
    )

    with open(global_all_sections_final_path_json, "w") as file:
        json.dump(
            global_sections.model_dump(mode="json", by_alias=True), file, indent=2
        )

    return global_sections


def contains_data(override: bool | None, path: Path, message: str) -> str | None:
    """
    Gets the data at the given path if it exists.
    If it exists and given override is true, then no data is returned.
    If override is None, then asks the user with the given message if they want to override it.
    """
    if not path.exists():
        return None

    if override is None:
        return _ask_override_for_path(path, message)

    if override:
        return None

    with open(path, "r") as f:
        return f.read()


def _ask_override_for_path(path: Path, message: str) -> str | None:
    """
    If override is None, ask the user if they want to override or not
    the data at the given path with the given message if there is data.
    Returns the existing data if no override and exists
    Any input other than y/Y is treated as false.
    """

    override = input(f"{message} Override? (y) ").lower().strip()

    if override == "y" or override == "":
        print(f"Overriding {path}")
        return None

    print("Using saved data.")
    with open(path, "r") as f:
        return f.read()


def get_professors_from_sections(parsed_sections: list[Section]) -> list[str]:
    """
    Get the list if unique professors from the parsed sections
    """
    profs: set[str] = set()

    for section in parsed_sections:
        profs.update(get_professors_from_section(section))

    return list(prof for prof in profs if prof.strip() != "")


def get_professors_from_section(section: Section) -> list[str]:
    """
    Gets the list of profs for the given section
    """
    return [leclab.prof for leclab in section.leclabs]


def get_saved_pids(pids_path: Path) -> dict[str, str | None]:
    """
    Gets the saved pids on the local dics
    """

    if not pids_path.exists():
        with open(pids_path, "w") as file:
            _ = file.write(json.dumps({}))

            return {}

    with open(pids_path, "r") as file:
        adapter = TypeAdapter(dict[str, str | None])
        return adapter.validate_json(file.read())


def to_sections_by_id(sections: list[Section]) -> OrderedDict[str, Section]:
    """
    Returns an ordered dict of the sections
    """
    return OrderedDict((section.id, section) for section in sections)

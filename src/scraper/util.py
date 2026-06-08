import json

from pydantic import TypeAdapter

from scraper.files import Files
from scraper.models import Rating, Section


def normalize_string(s: str):
    s = s.replace("\u00e9", "e").replace("é", "e")  #  removes é
    s = s.replace("\u00c9", "E").replace("É", "E")  #  removes É
    s = s.replace("\u00e8", "e").replace("è", "e")  #  removes è
    s = s.replace("\u00e2", "a").replace("â", "a")  #  removes â
    s = s.replace("\u00e7", "c").replace("ç", "c")  #  removes ç
    s = s.replace("\u00e0", "a").replace("à", "a")  #  removes à
    s = s.replace("\u0000", "")  #  removes null character

    return s


def add_rating_to_sections(files: Files):
    with open(files.all_sections_final_path_json, "r") as file:
        sections = TypeAdapter(list[Section]).validate_json(file.read())

    with open(files.ratings_path, "r") as file:
        ratings = [Rating.model_validate(r) for r in json.load(file)]

    ratings_by_prof = {rating.prof: rating for rating in ratings}

    updated_sections = [
        section.model_copy(
            update={
                "leclabs": [
                    leclab.model_copy(
                        update={"rating": ratings_by_prof.get(leclab.prof)}
                    )
                    for leclab in section.leclabs
                ]
            }
        )
        for section in sections
    ]

    with open(files.all_sections_final_path_json, "w") as file:
        _ = file.write(
            json.dumps(
                [
                    section.model_dump(mode="json", by_alias=True)
                    for section in updated_sections
                ],
                indent=2,
            )
        )

import json


from scraper.files import Files
from scraper.models import Rating


def normalize_string(s: str):
    s = s.replace("\u00e9", "e").replace("é", "e")  #  removes é
    s = s.replace("\u00c9", "E").replace("É", "E")  #  removes É
    s = s.replace("\u00e8", "e").replace("è", "e")  #  removes è
    s = s.replace("\u00e2", "a").replace("â", "a")  #  removes â
    s = s.replace("\u00e7", "c").replace("ç", "c")  #  removes ç
    s = s.replace("\u00e0", "a").replace("à", "a")  #  removes à
    s = s.replace("\u0000", "")  #  removes null character

    return s


def make_sections_final(files: Files):
    """
    Adds teacher ratings to each section
    Writes to the final json {sectionId: Section}
    """

    sections = files.get_parsed_sections_file_content()

    with open(files.ratings_path, "r") as file:
        ratings = [Rating.model_validate(r) for r in json.load(file)]

    ratings_by_prof = {rating.prof: rating for rating in ratings}

    for section in sections:
        for leclab in section.leclabs:
            leclab.rating = ratings_by_prof.get(leclab.prof)

    sections_dict = {
        section.id: section.model_dump(mode="json", by_alias=True)
        for section in sections
    }

    with open(files.all_sections_final_path_json, "w") as file:
        json.dump(
            sections_dict,
            file,
            indent=2,
        )

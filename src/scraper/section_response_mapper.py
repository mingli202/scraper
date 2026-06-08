from .models import Section, Section


def sections_to_section_responses(sections: list[Section]) -> list[Section]:
    section_responses: list[Section] = []
    leclab_id = 1
    day_time_id = 1

    for section_id, section in enumerate(sections, start=1):
        leclabs: list[dict[str, object]] = []

        for leclab in section.leclabs:
            day_times: list[dict[str, object]] = []

            for day_time in leclab.day_times:
                day_times.append(
                    {
                        "id": day_time_id,
                        "day": day_time.day,
                        "start_time_hhmm": day_time.start_time_hhmm,
                        "end_time_hhmm": day_time.end_time_hhmm,
                        "leclab_id": leclab_id,
                    }
                )
                day_time_id += 1

            leclabs.append(
                {
                    "id": leclab_id,
                    "title": leclab.title,
                    "type": leclab.type,
                    "section_id": section_id,
                    "prof": leclab.prof,
                    "rating": None,
                    "day_times": day_times,
                }
            )
            leclab_id += 1

        section_responses.append(
            Section.model_validate(
                {
                    "id": section_id,
                    "course": section.course,
                    "section": section.section,
                    "domain": section.domain,
                    "code": section.code,
                    "title": section.title,
                    "leclabs": leclabs,
                    "more": section.more,
                    "view_data": section.view_data,
                }
            )
        )

    return section_responses

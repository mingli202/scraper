import sqlite3

from scraper import files


if __name__ == "__main__":
    files = files.Files()
    conn = sqlite3.connect(files.all_sections_final_path)
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT * FROM sections
        INNER JOIN times ON sections.id = times.section_id
    """).fetchmany(5)

    print(rows)

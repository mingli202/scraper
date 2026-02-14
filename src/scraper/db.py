from sqlmodel import SQLModel, create_engine
from scraper.files import Files


file = Files()

sqlite_url = f"sqlite:///{file.all_sections_final_path}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

SQLModel.metadata.create_all(engine)

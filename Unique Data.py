from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
connection_string = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?charset=utf8mb4"
)
engine = create_engine(connection_string)

with engine.connect() as conn:
    for table, col in [
        ("Employees", "Gender"), ("Employees", "Mine"), ("Employees", "Department"),
        ("Employees", "JobTitle"), ("Employees", "Shift"),
        ("Equipment", "Category"), ("Equipment", "Manufacturer"),
        ("Equipment", "Status"), ("Equipment", "Mine"),
        ("Production", "Mine"), ("Production", "Shift"),
    ]:
        rows = conn.execute(text(f"SELECT DISTINCT `{col}` FROM `{table}`")).fetchall()
        values = [r[0] for r in rows]
        print(f"{table}.{col}: {values}")
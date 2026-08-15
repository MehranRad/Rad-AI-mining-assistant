from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
connection_string = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?connect_timeout=10"
)
engine = create_engine(connection_string)

with engine.connect() as conn:
    rows = conn.execute(text("DESCRIBE AuditLog")).fetchall()
    for r in rows:
        print(r)
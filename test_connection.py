import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

print(f"Testing connection to {DB_HOST}:{DB_PORT} ...")

# ---- Attempt 1: WITHOUT SSL ----
print("\n[Attempt 1] Connecting WITHOUT SSL...")
try:
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME,
        connect_timeout=15,
    )
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("SUCCESS (no SSL). Query result:", cursor.fetchone())
    conn.close()
except Exception as e:
    print("FAILED (no SSL):", e)

# ---- Attempt 2: WITH SSL (only relevant if a ca.pem file exists) ----
print("\n[Attempt 2] Connecting WITH SSL (using ca.pem)...")
try:
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME,
        ssl={"ca": "ca.pem"},
        connect_timeout=15,
    )
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("SUCCESS (with SSL). Query result:", cursor.fetchone())
    conn.close()
except Exception as e:
    print("FAILED (with SSL):", e)
"""
Checks that the categorical constants in schema_constants.py match the actual
data.

By default it compares against the cleaned Excel source files (data/*.xlsx)
using the same normalization load_data.py applies. With --db it compares
against the live MySQL database instead (the values as actually stored, which
is what SQL queries match against).

Usage:
    python check_schema_consistency.py            # Excel only
    python check_schema_consistency.py --db       # live MySQL only

Exit code is non-zero if any mismatch is found.
"""
import argparse

import pandas as pd

import schema_constants as sc

# Cleaning mode applied to each Excel column before comparing, mirroring the
# normalization load_data.py performs before writing rows into MySQL.
EXCEL_CLEAN = {
    "Employees": {
        "Gender": "strip",
        "Mine": "strip",
        "Department": "strip",
        "JobTitle": "strip",
        "Shift": "shift_fill_unknown",
    },
    "Equipment": {
        "Mine": "strip",
        "Status": "strip",
        "Category": "category_title",
        "Manufacturer": "strip",
    },
    "Production": {
        "Mine": "strip",
        "Shift": "strip",
    },
}

CHECKS = [
    ("Employees", "Gender", sc.GENDERS),
    ("Employees", "Mine", sc.MINES),
    ("Employees", "Department", sc.DEPARTMENTS),
    ("Employees", "JobTitle", sc.JOB_TITLES),
    ("Employees", "Shift", sc.EMPLOYEE_SHIFTS),
    ("Equipment", "Mine", sc.MINES),
    ("Equipment", "Status", sc.EQUIPMENT_STATUSES),
    ("Equipment", "Category", sc.EQUIPMENT_CATEGORIES),
    ("Equipment", "Manufacturer", sc.EQUIPMENT_MANUFACTURERS),
    ("Production", "Mine", sc.MINES),
    ("Production", "Shift", sc.PRODUCTION_SHIFTS),
]


def clean_series(series, mode):
    s = series.copy()
    if mode == "shift_fill_unknown":
        s = s.fillna("Unknown")
    s = s.astype(str).str.strip()
    if mode == "shift_fill_unknown":
        s = s.replace("", "Unknown")
    if mode == "category_title":
        s = s.str.title()
    return set(s)


def compare(table, column, expected, actual):
    exp = set(expected)
    missing = sorted(exp - actual)
    extra = sorted(actual - exp)
    if missing or extra:
        print(f"[MISMATCH] {table}.{column}")
        if missing:
            print(f"  documented but NOT in data: {missing}")
        if extra:
            print(f"  in data but NOT documented: {extra}")
        return 1
    print(f"[OK] {table}.{column}: {len(exp)} value(s) match")
    return 0


def check_excel() -> int:
    errors = 0
    for table, column, expected in CHECKS:
        df = pd.read_excel(f"data/{table}.xlsx")
        actual = clean_series(df[column], EXCEL_CLEAN[table][column])
        errors += compare(table, column, expected, actual)
    return errors


def check_db() -> int:
    from sqlalchemy import text
    from chat_storage import storage_engine

    errors = 0
    with storage_engine.connect() as conn:
        for table, column, expected in CHECKS:
            rows = conn.execute(text(f"SELECT DISTINCT `{column}` FROM `{table}`")).fetchall()
            actual = {r[0] for r in rows}
            errors += compare(table, column, expected, actual)
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        action="store_true",
        help="compare against the live MySQL database instead of the Excel files",
    )
    args = parser.parse_args()

    total = check_db() if args.db else check_excel()
    print(f"\n{'ALL CONSTANTS CONSISTENT' if total == 0 else f'{total} MISMATCH(ES) FOUND'}")
    raise SystemExit(1 if total else 0)
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os
import time

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

connection_string = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?connect_timeout=10&charset=utf8mb4"
)

engine = create_engine(connection_string, poolclass=NullPool)


def upload_with_retry(df, table_name, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            df.to_sql(table_name, engine, if_exists="append", index=False, chunksize=200)
            print(f"{table_name} uploaded successfully.")
            return True
        except Exception as e:
            print(f"Attempt {attempt}/{max_retries} failed for {table_name}: {e}")
            engine.dispose()
            if attempt < max_retries:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"FAILED to upload {table_name} after {max_retries} attempts.")
                return False


employees = pd.read_excel("data/Employees.xlsx")
equipment = pd.read_excel("data/Equipment.xlsx")
production = pd.read_excel("data/Production.xlsx")

print("=" * 60)
print("STEP 1: Checking for duplicate primary keys")
print("=" * 60)

def check_and_remove_duplicates(df, key_column, table_name):
    duplicates = df[df.duplicated(subset=[key_column], keep=False)]
    if len(duplicates) > 0:
        print(f"\n[{table_name}] Found {len(duplicates)} duplicate rows on '{key_column}':")
        print(duplicates.sort_values(key_column))
        df_clean = df.drop_duplicates(subset=[key_column], keep="first")
        removed = len(df) - len(df_clean)
        print(f"[{table_name}] Removed {removed} duplicate row(s). Remaining: {len(df_clean)}")
        return df_clean
    else:
        print(f"\n[{table_name}] No duplicates found on '{key_column}'. Total rows: {len(df)}")
        return df

employees = check_and_remove_duplicates(employees, "EmployeeID", "Employees")
equipment = check_and_remove_duplicates(equipment, "EquipmentID", "Equipment")
production = check_and_remove_duplicates(production, "ProductionID", "Production")

print("\n" + "=" * 60)
print("STEP 2: Cleaning data")
print("=" * 60)

# NOTE: Persian text has no upper/lower case, so .str.title()/.str.upper()
# (used in the original English-language version of this script) no longer
# applies. We only strip stray leading/trailing whitespace here — the same
# kind of light messiness ("  Sungun ") that existed in the English data
# also appears in this Persian data ("  مکانیک  ", " سرچشمه").
def clean_text_column(series):
    return series.astype(str).str.strip()

employees["Mine"] = clean_text_column(employees["Mine"])
employees["Department"] = clean_text_column(employees["Department"])
employees["Gender"] = clean_text_column(employees["Gender"])
employees["JobTitle"] = clean_text_column(employees["JobTitle"])
# Missing cells in an object-dtype column come through as Python None,
# not numpy NaN — so fillna() must run BEFORE astype(str), or str(None)
# ends up stored as the literal text "None". Matches the original
# English-language script's convention of defaulting missing Shift to
# "Unknown".
employees["Shift"] = employees["Shift"].fillna("Unknown")
employees["Shift"] = clean_text_column(employees["Shift"]).replace("", "Unknown")
employees["FirstName"] = clean_text_column(employees["FirstName"])
employees["LastName"] = clean_text_column(employees["LastName"])
employees["HireDate"] = pd.to_datetime(employees["HireDate"], errors="coerce")

# Category is an equipment TYPE name, which — unlike Mine/Department/
# JobTitle — stays in English even in this Persian dataset (real
# equipment types are conventionally referred to in English). So,
# unlike the Persian columns, it still needs case normalization
# (this is what fixes "truck" -> "Truck"), same as the original
# English-only script did. Manufacturer is intentionally left as-is
# (not title-cased) because brand names like "ThyssenKrupp"/"XCMG"/
# "SANY" have meaningful internal capitalization that .title() would
# destroy (e.g. "ThyssenKrupp" -> "Thyssenkrupp") — this matches the
# original script too, which never title-cased Manufacturer.
equipment["Category"] = clean_text_column(equipment["Category"]).str.title()
equipment["Mine"] = clean_text_column(equipment["Mine"])
equipment["Manufacturer"] = clean_text_column(equipment["Manufacturer"])
equipment["Status"] = clean_text_column(equipment["Status"])
equipment["InstallDate"] = pd.to_datetime(equipment["InstallDate"], errors="coerce")

production["Mine"] = clean_text_column(production["Mine"])
production["Shift"] = clean_text_column(production["Shift"])
production["Date"] = pd.to_datetime(production["Date"], errors="coerce")

print("Data cleaning completed.")

print("\n" + "=" * 60)
print("STEP 3: Checking for orphan foreign keys (optional diagnostics)")
print("=" * 60)

valid_equipment_ids = set(equipment["EquipmentID"])
valid_employee_ids = set(employees["EmployeeID"])

orphan_equipment = production[~production["EquipmentID"].isin(valid_equipment_ids)]
orphan_operators = production[~production["OperatorID"].isin(valid_employee_ids)]

if len(orphan_equipment) > 0:
    print(f"WARNING: {len(orphan_equipment)} Production rows reference an EquipmentID not found in Equipment table.")
if len(orphan_operators) > 0:
    print(f"WARNING: {len(orphan_operators)} Production rows reference an OperatorID not found in Employees table.")
if len(orphan_equipment) == 0 and len(orphan_operators) == 0:
    print("No orphan foreign keys found. Data is consistent.")

print("\n" + "=" * 60)
print("STEP 4: Creating tables with Primary Keys")
print("=" * 60)

CREATE_TABLES_SQL = {
    "Employees": """
        CREATE TABLE IF NOT EXISTS Employees (
            EmployeeID BIGINT PRIMARY KEY,
            FirstName TEXT,
            LastName TEXT,
            Gender TEXT,
            Age FLOAT,
            Department TEXT,
            JobTitle TEXT,
            Mine TEXT,
            HireDate DATETIME,
            Salary FLOAT,
            OvertimeHours FLOAT,
            OvertimePay FLOAT,
            Shift TEXT
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_persian_ci
    """,
    "Equipment": """
        CREATE TABLE IF NOT EXISTS Equipment (
            EquipmentID BIGINT PRIMARY KEY,
            EquipmentCode TEXT,
            EquipmentName TEXT,
            Category TEXT,
            Mine TEXT,
            Manufacturer TEXT,
            InstallDate DATETIME,
            PurchasePrice FLOAT,
            Status TEXT,
            ExpectedLifeYears FLOAT
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_persian_ci
    """,
    "Production": """
        CREATE TABLE IF NOT EXISTS Production (
            ProductionID BIGINT PRIMARY KEY,
            Date DATETIME,
            Mine TEXT,
            EquipmentID BIGINT,
            OperatorID BIGINT,
            Shift TEXT,
            CopperOreTon FLOAT,
            CopperConcentrateTon FLOAT,
            RecoveryRate FLOAT,
            WorkingHours FLOAT,
            DowntimeHours FLOAT,
            EnergyConsumption FLOAT,
            FuelConsumption FLOAT
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_persian_ci
    """
}

def create_tables_with_retry(max_retries=5):
    for attempt in range(1, max_retries + 1):
        try:
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE IF EXISTS Production"))
                conn.execute(text("DROP TABLE IF EXISTS Equipment"))
                conn.execute(text("DROP TABLE IF EXISTS Employees"))

                conn.execute(text(CREATE_TABLES_SQL["Employees"]))
                conn.execute(text(CREATE_TABLES_SQL["Equipment"]))
                conn.execute(text(CREATE_TABLES_SQL["Production"]))
            print("Tables created successfully.")
            return True
        except Exception as e:
            print(f"Attempt {attempt}/{max_retries} failed: {e}")
            engine.dispose()
            if attempt < max_retries:
                wait_time = 5 * attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    print("FAILED to create tables after all retry attempts.")
    return False


tables_created = create_tables_with_retry()

if not tables_created:
    print("\nStopping here — could not create tables due to persistent connection issues.")
else:
    print("\n" + "=" * 60)
    print("STEP 5: Uploading data")
    print("=" * 60)

    ok1 = upload_with_retry(employees, "Employees")
    ok2 = upload_with_retry(equipment, "Equipment")
    ok3 = upload_with_retry(production, "Production")

    if ok1 and ok2 and ok3:
        print("\nSUCCESS: All data uploaded to the database.")
        print(f"Employee records: {len(employees)}")
        print(f"Equipment records: {len(equipment)}")
        print(f"Production records: {len(production)}")
    else:
        print("\nWARNING: One or more tables failed to fully upload. Check messages above.")
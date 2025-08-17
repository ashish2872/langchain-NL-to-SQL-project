import os
import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import re
from models import get_tables_in_order
user = os.getenv("USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
port = os.getenv("PORT")
dbname = os.getenv("DATABASE")



# ---------- Database Setup ----------
DATABASE_URL = "postgresql+psycopg2://postgres:ashish6677@34.30.63.17:5432/postgres"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def load_csv_to_db(file_path, table_name):
    """
    Reads CSV and inserts data into Postgres table with length validation.
    """
    print(f"📂 Loading {file_path} into table '{table_name}'")

    # 1. Read CSV
    df = pd.read_csv(file_path)

    # 2. Get DB column max lengths for VARCHAR columns
    inspector = inspect(engine)
    columns_info = inspector.get_columns(table_name)
    varchar_limits = {
        col["name"]: int(re.search(r"\((\d+)\)", str(col["type"])).group(1))
        for col in columns_info
        if "VARCHAR" in str(col["type"]).upper()
    }

    # 3. Trim only values exceeding VARCHAR limits
    for col, limit in varchar_limits.items():
        if col in df.columns:
            df[col] = df[col].astype(str).apply(lambda x: x[:limit] if len(x) > limit else x)

    # 4. Push to DB (append to existing table)
    df.to_sql(table_name, engine, if_exists="append", index=False)

    print(f"✅ Inserted {len(df)} rows into {table_name}")

# ---------- Load all CSVs in schema order ----------
def get_tables_in_order():
    """
    Replace with your actual table order function.
    Must return list of table names in the order they should be loaded.
    """
    return ["companies", "employees", "departments"]  # example

def load_all_csvs(csv_folder):
    table_order = get_tables_in_order()
    for table in table_order:
        csv_file = os.path.join(csv_folder, f"{table}.csv")
        if os.path.exists(csv_file):
            load_csv_to_db(csv_file, table)
        else:
            print(f"⚠️ No CSV found for table '{table}'")

# Example usage:
load_all_csvs("dummy_data_folder")

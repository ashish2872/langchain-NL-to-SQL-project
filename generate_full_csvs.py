"""
generate_full_csvs.py

Generates CSVs with 50 rows for every table in the SQLAlchemy schema defined
in models.py. Uses Faker to populate realistic-looking values and ensures
foreign-key references are consistent by generating parent-table IDs first.

Assumptions:
- models.py is in the same directory and defines all SQLAlchemy models from your schema.
- models.py exposes: Base and get_tables_in_order() (if not, the script will fallback to Base.metadata.sorted_tables()).
- Most PKs are UUIDs (as in your schema) and will be exported as strings.
"""

import csv
import decimal
import random
import uuid
from pathlib import Path
import os
from datetime import date, datetime, timedelta

from faker import Faker
from sqlalchemy import Integer, String, Text, Boolean, Date, DateTime, Numeric, Float
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# Import models (your schema file)
# Ensure models.py is in same directory and contains the classes & Base
import models  # <- your schema file (the one you pasted). MUST be named models.py
current_dir = os.getcwd()
fake = Faker()
OUTPUT_DIR = Path("dummy_data_full")
OUTPUT_DIR.mkdir(exist_ok=True)

NUM_ROWS = 50

# Keep track of generated primary key values per table for FK population
pk_values = {}  # {table_name: [list_of_pk_values_as_strings_or_ints]}

def is_uuid_col(col):
    # detect PostgreSQL UUID or generic type that uses UUID
    return isinstance(col.type, PG_UUID) or getattr(col.type, "__class__", None).__name__.lower().startswith("uuid")

def is_integer_col(col):
    return isinstance(col.type, Integer)

def is_string_col(col):
    return isinstance(col.type, (String, Text))

def is_boolean_col(col):
    return isinstance(col.type, Boolean)

def is_date_col(col):
    return isinstance(col.type, Date)

def is_datetime_col(col):
    return isinstance(col.type, DateTime)

def is_numeric_col(col):
    return isinstance(col.type, Numeric) or isinstance(col.type, Float)

def random_decimal(scale=2, max_whole=99999):
    # return Decimal with given scale
    whole = random.randint(0, max_whole)
    frac = random.randint(0, 10**scale - 1)
    val = decimal.Decimal(f"{whole}.{str(frac).zfill(scale)}")
    return val

def random_date(start_year=2019, end_year=2025):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(0, delta)))

def get_tables_order():
    # Prefer get_tables_in_order if present
    if hasattr(models, "get_tables_in_order"):
        try:
            ordered = models.get_tables_in_order()
            # Accept if it's a list of classes
            if isinstance(ordered, (list, tuple)) and len(ordered) > 0:
                return ordered
        except Exception:
            pass
    # Fallback to metadata sorted_tables
    return [models.Base.metadata.tables[name].metadata.tables[name].class_ 
            if hasattr(models.Base.metadata.tables[name], "class_") else models.Base.metadata.tables[name]
            for name in models.Base.metadata.sorted_tables]

def table_name_for(model_or_table):
    # model class -> __tablename__ or SQLAlchemy Table -> name
    if hasattr(model_or_table, "__tablename__"):
        return model_or_table.__tablename__
    if hasattr(model_or_table, "name"):
        return model_or_table.name
    return str(model_or_table)

def get_columns_for_table(model):
    # Accept a model class; find its __table__ columns
    table = getattr(model, "__table__", None)
    if table is None:
        return []
    # return list of Column objects
    return list(table.columns)

def get_primary_key_column(model):
    cols = get_columns_for_table(model)
    for c in cols:
        if c.primary_key:
            return c
    return None

def get_foreign_keys(col):
    # returns list of (referred_table_name, referred_column_name)
    fks = []
    for fk in col.foreign_keys:
        # fk.column is a Column object for referenced column
        ref_col = fk.column
        ref_table = ref_col.table.name
        fks.append((ref_table, ref_col.name))
    return fks

def generate_value_for_column(col, table_name):
    # If column has a FK, we'll set this value by selecting from pk_values of the parent table
    fks = get_foreign_keys(col)
    if fks:
        # Choose first FK (most schemas have single FK per column)
        ref_table, ref_col = fks[0]
        if ref_table not in pk_values or not pk_values[ref_table]:
            # No parent IDs yet (shouldn't happen if ordering is correct). As fallback create a new UUID
            if is_uuid_col(col):
                return str(uuid.uuid4())
            if is_integer_col(col):
                return random.randint(1, NUM_ROWS * 10)
            return None
        return random.choice(pk_values[ref_table])

    # No FK: generate based on column type & name hints
    col_name = col.name.lower()

    if is_uuid_col(col):
        return str(uuid.uuid4())
    if is_integer_col(col):
        # primary keys and counters
        return random.randint(1, NUM_ROWS * 10)
    if is_boolean_col(col):
        # default bias to True 30% or False 70% depending on name
        if "is_" in col_name or col_name.startswith("has_") or col_name.endswith("_active"):
            return random.choice([True, False])
        return random.choice([True, False])
    if is_date_col(col):
        return random_date().isoformat()
    if is_datetime_col(col):
        # realistic timestamp
        dt = fake.date_time_between(start_date='-3y', end_date='now')
        return dt.isoformat(sep=' ')
    if is_numeric_col(col):
        # choose scale based on declared precision if available
        if hasattr(col.type, 'scale') and col.type.scale is not None:
            sc = col.type.scale
            return str(random_decimal(scale=sc))
        # fallback decimal with 2 places
        return str(random_decimal(scale=2))

    # Strings / Text: heuristics by column name
    if "name" == col_name or col_name.endswith("_name") or "company" in col_name or "vendor" in col_name:
        return fake.company() if "company" in col_name else fake.name()
    if "email" in col_name:
        return fake.safe_email()
    if "phone" in col_name or "mobile" in col_name or "contact" in col_name:
        return fake.phone_number()
    if "address" in col_name or "line" in col_name or "street" in col_name:
        return fake.street_address()
    if "city" in col_name:
        return fake.city()
    if "state" in col_name:
        return fake.state()
    if "country" in col_name:
        return fake.country()
    if "pin" in col_name or "postal" in col_name or "postcode" in col_name:
        return fake.postcode()
    if "gst" in col_name or "pan" in col_name or "hsn" in col_name or "cin" in col_name:
        return fake.bothify(text='??#########')[:15]  # adhoc
    if "status" in col_name:
        # plausible statuses
        return random.choice(["active", "inactive", "pending", "confirmed", "draft", "paid", "unpaid", "cancelled"])
    if "type" in col_name:
        return random.choice(["asset", "liability", "expense", "income", "equity", "debit", "credit"])
    if "description" in col_name or "notes" in col_name:
        return fake.paragraph(nb_sentences=2)
    if "code" in col_name or "sku" in col_name or "asset_number" in col_name:
        return fake.bothify(text='???-#####')
    if "otp" in col_name:
        return fake.random_number(digits=6, fix_len=True)
    # default fallback
    # if column has length constraint, try to respect it
    if hasattr(col.type, 'length') and col.type.length:
        return fake.text(max_nb_chars=min(200, col.type.length))[:col.type.length]
    # generic short text
    return fake.word()

def row_to_csv_value(value):
    # Convert Python objects to CSV-safe strings
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (decimal.Decimal, float)):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)

def write_csv_for_table(table_name, columns, rows):
    filename = OUTPUT_DIR / f"{table_name}.csv"
    fieldnames = [c.name for c in columns]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            # convert all values to csv-friendly strings
            out = {k: row_to_csv_value(v) for k, v in r.items()}
            writer.writerow(out)

def main():
    print("Starting CSV generation...")
    # Determine table order (list of model classes or Table objects)
    ordered_models = get_tables_order()

    # If get_tables_order returned SQLAlchemy Table objects rather than model classes,
    # we need to handle accordingly. We'll build a list of (table_name, columns list, pk column)
    ordered_tables = []
    for m in ordered_models:
        # m might be a mapped class or a Table
        if hasattr(m, "__table__"):
            tbl = m.__table__
        else:
            tbl = m if hasattr(m, "columns") else None
        if tbl is None:
            continue
        ordered_tables.append(tbl)

    for tbl in ordered_tables:
        table_name = tbl.name
        print(f"Generating for table: {table_name}")
        columns = list(tbl.columns)

        # Identify PK column(s)
        pk_cols = [c for c in columns if c.primary_key]
        pk_col = pk_cols[0] if pk_cols else None
        pk_values.setdefault(table_name, [])

        rows = []
        for i in range(NUM_ROWS):
            row = {}
            # For deterministic-ish reproducibility, you could set seed here: fake.seed_instance(i)
            for col in columns:
                # Skip server-default columns? We'll still produce values for them.
                # If column is PK and is autoincrement integer, produce sequential ints
                if col.primary_key and is_integer_col(col):
                    # try to create sequential integer PKs starting at 1
                    val = i + 1
                    row[col.name] = val
                else:
                    val = generate_value_for_column(col, table_name)
                    # If column is numeric type but our generator returned str, convert to Decimal/string representation
                    if is_numeric_col(col):
                        # ensure decimal string
                        row[col.name] = str(val)
                    else:
                        row[col.name] = val
            # Save PK for FK usage later
            if pk_col is not None:
                pk_val = row.get(pk_col.name)
                # If pk is None (rare), create uuid
                if pk_val is None:
                    if is_uuid_col(pk_col):
                        pk_val = str(uuid.uuid4())
                        row[pk_col.name] = pk_val
                    elif is_integer_col(pk_col):
                        pk_val = i + 1
                        row[pk_col.name] = pk_val
                pk_values[table_name].append(pk_val)
            rows.append(row)

        # Write CSV
        write_csv_for_table(table_name, columns, rows)
        print(f"  -> Wrote {NUM_ROWS} rows to {OUTPUT_DIR / (table_name + '.csv')}")
    print("Done. All CSVs written to:", OUTPUT_DIR.resolve())

if __name__ == "__main__":
    main()

import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import *  # import all your models
from dotenv import load_dotenv
ENV_FILE = ".env"
load_dotenv(ENV_FILE)


# --------------------
# 1️⃣ Database connection
# --------------------
DB_USER = os.getenv("USER")
DB_PASS = os.getenv("PASSWORD")
DB_NAME = os.getenv("DATABASE")
DB_HOST = os.getenv("HOST")  # e.g. "34.93.xx.xx" or private IP
DB_PORT = os.getenv("PORT", "5432")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# --------------------
# 2️⃣ Helper to load CSV into DB
# --------------------
def load_csv_to_db(model, csv_path):
    if not os.path.exists(csv_path):
        print(f"⚠️ Skipping {model.__tablename__}, no CSV found.")
        return
    
    df = pd.read_csv(csv_path)
    df = df.where(pd.notnull(df), None)  # Replace NaN with None for SQLAlchemy

    objects = [model(**row) for row in df.to_dict(orient="records")]
    if objects:
        session.bulk_save_objects(objects)
        session.commit()
        print(f"✅ Inserted {len(objects)} into {model.__tablename__}")
    else:
        print(f"⚠️ No data in {csv_path}")

# --------------------
# 3️⃣ Loop through tables in dependency order
# --------------------
if __name__ == "__main__":
    try:
        for model in get_tables_in_order():
            model_name = model.__tablename__
            csv_path = f"dummy_data_full/{model_name}.csv"
            load_csv_to_db(model, csv_path)

        print("🎉 All CSVs imported successfully in dependency order!")
    except Exception as e:
        session.rollback()
        print(f"❌ Error importing CSVs: {e}")
    finally:
        session.close()
"""Optional: export your own hospital_db tables to data/*.csv for the online demo.

Only use this if your data is synthetic (for example the Kaggle "Healthcare Dataset").
Never publish real patient records. Without data/*.csv the demo uses made-up sample data.

Run from the repository root (where .streamlit/secrets.toml is):
    python tools/export_data.py
The three CSV files are written to data/, which the online demo uses instead of sample data.
"""
import tomllib
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

cfg = tomllib.loads(Path(".streamlit/secrets.toml").read_text())["mysql"]   # run from the repo root
engine = create_engine(URL.create("mysql+pymysql", username=cfg["user"], password=cfg["password"],
                                  host=cfg["host"], port=cfg["port"], database=cfg["database"]))
out = Path("data")
out.mkdir(exist_ok=True)
for table in ["patients", "admissions", "billings"]:
    df = pd.read_sql(f"SELECT * FROM {table}", engine)
    df.to_csv(out / f"{table}.csv", index=False)
    print(f"{table}: {len(df):,} rows -> data/{table}.csv")

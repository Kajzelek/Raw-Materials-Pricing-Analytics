from os import getenv
from pathlib import Path

import psycopg2
import pandas as pd
from dotenv import load_dotenv
from transform import run_transform

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

DB_PASSWORD = getenv("DB_PASSWORD") or getenv("POSTGRES_PASSWORD") or "change_me"

DB_CONFIG = {
    "host": "localhost",
    "database": "pricing_intelligence",
    "user": "postgres",
    "password": DB_PASSWORD,
    "port": 5432
}


def load_data_to_core(df: pd.DataFrame):
    if df is None or df.empty:
        print("No data to load.")
        return

    upsert_query = """
                   INSERT INTO fct_daily_market_prices (price_date, commodity_code, currency_code, price_in_currency, \
                                                        price_pln, is_anomaly) \
                   VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (price_date, commodity_code, currency_code) 
        DO \
                   UPDATE SET
                       price_in_currency = EXCLUDED.price_in_currency, \
                       price_pln = EXCLUDED.price_pln, \
                       is_anomaly = EXCLUDED.is_anomaly, \
                       created_at = CURRENT_TIMESTAMP; \
                   """

    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        rows_inserted = 0
        for _, row in df.iterrows():
            cur.execute(upsert_query, (
                row['price_date'],
                row['commodity_code'],
                row['currency_code'],
                row['price_in_currency'],
                row['price_pln'],
                row['is_anomaly']
            ))
            rows_inserted += 1

        conn.commit()
        print(f"Successfully loaded/updated {rows_inserted} records into fct_daily_market_prices.")
    except Exception as e:
        print(f"Error during Load phase: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    transformed_df = run_transform()
    load_data_to_core(transformed_df)
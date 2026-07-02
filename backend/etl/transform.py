from os import getenv

import psycopg2
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

DB_PASSWORD = getenv("DB_PASSWORD") or getenv("POSTGRES_PASSWORD") or "change_me"
API_KEY = getenv("API_KEY")

DB_CONFIG = {
    "host": "localhost",
    "database": "pricing_intelligence",
    "user": "postgres",
    "password": DB_PASSWORD,
    "port": 5432
}


def get_latest_json_from_staging(source_api: str):
    query = """
             SELECT raw_json \
             FROM staging_raw_api_responses
             WHERE source_api = %s
             ORDER BY fetch_ts DESC LIMIT 1; \
             """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query, (source_api,))
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"Error fetching {source_api}: {e}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def run_transform():
    print("Starting Transformation phase with Pandas...")

    fx_json = get_latest_json_from_staging("Frankfurter API")
    commodity_json = get_latest_json_from_staging("CommodityPriceAPI")

    if not fx_json or not commodity_json:
        print("Missing data in staging area. Aborting.")
        return None

    pln_to_usd = fx_json["rates"]["USD"]
    usd_to_pln = round(1 / pln_to_usd, 4)
    print(f"Calculated Exchange Rate: 1 USD = {usd_to_pln} PLN")

    commodity_rates = commodity_json["rates"]

    raw_data = []
    today = datetime.now().date()

    for code, price_usd in commodity_rates.items():
        price_pln = round(price_usd * usd_to_pln, 4)

        is_anomaly = False
        if code == "XAU" and price_usd > 2400:
            is_anomaly = True
        elif code == "XAG" and price_usd > 30:
            is_anomaly = True

        raw_data.append({
            "price_date": today,
            "commodity_code": code,
            "currency_code": "USD",
            "price_in_currency": price_usd,
            "price_pln": price_pln,
            "is_anomaly": is_anomaly
        })

    df = pd.DataFrame(raw_data)
    print("\nTransformed Data (Pandas DataFrame)")
    print(df.to_string(index=False))

    return df


if __name__ == "__main__":
    run_transform()
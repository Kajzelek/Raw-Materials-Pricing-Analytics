from os import getenv
from pathlib import Path

import requests
import json
import psycopg2
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env.example")

DB_PASSWORD = getenv("DB_PASSWORD") or getenv("POSTGRES_PASSWORD") or "change_me"
API_KEY = getenv("API_KEY")

DB_CONFIG = {
    "host": "localhost",
    "database": "pricing_intelligence",
    "user": "postgres",
    "password": DB_PASSWORD,
    "port": 5432
}


def save_to_staging(source_api: str, raw_data: dict):
    """Zapisuje nienaruszony, surowy JSON z API do bazy """
    query = """
            INSERT INTO staging_raw_api_responses (source_api, raw_json)
            VALUES (%s, %s); \
            """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query, (source_api, json.dumps(raw_data)))
        conn.commit()
        print(f" Successfully saved raw data from {source_api} to staging.")
    except Exception as e:
        print(f" Error saving to staging ({source_api}): {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def extract_currency_rates():
    """Pobiera realne kursy walut z Frankfurter API"""
    url = "https://api.frankfurter.app/latest?from=PLN&to=USD,EUR"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            save_to_staging("Frankfurter API", data)
            return data
        else:
            print(f" Frankfurter API returned status code {response.status_code}")
    except Exception as e:
        print(f" Connection error with Frankfurter API: {e}")
    return None


def extract_commodity_prices():
    """Pobiera realne ceny surowców z CommodityPriceAPI"""

    if not API_KEY:
        print(" API key is missing; skipping CommodityPriceAPI extraction.")
        return None

    url = "https://api.commoditypriceapi.com/v2/rates/latest?symbols=xau,xag"

    headers = {
        "x-api-key": API_KEY
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                save_to_staging("CommodityPriceAPI", data)
                return data
            else:
                print(f" API Internal Error: {data}")
        else:
            print(f" CommodityPriceAPI returned status code {response.status_code}")
            print(f"Response body for debug: {response.text}")
    except Exception as e:
        print(f" Connection error with CommodityPriceAPI: {e}")
    return None


if __name__ == "__main__":
    print(" Starting Production Extraction phase...")
    extract_currency_rates()
    extract_commodity_prices()
    print(" Extraction phase finished.")
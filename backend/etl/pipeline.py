from extract import extract_currency_rates, extract_commodity_prices
from transform import run_transform
from load import load_data_to_core


def run_pipeline():
    print("Starting Full ETL Pipeline")

    extract_currency_rates()
    extract_commodity_prices()

    df = run_transform()

    load_data_to_core(df)

    print("ETL Pipeline Completed Successfully")


if __name__ == "__main__":
    run_pipeline()
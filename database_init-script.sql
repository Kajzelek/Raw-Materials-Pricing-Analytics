-- Raw Data
CREATE TABLE IF NOT EXISTS staging_raw_api_responses (
    id SERIAL PRIMARY KEY,
    source_api VARCHAR(100) NOT NULL, -- np. 'Frankfurter API', 'Commodities API'
    fetch_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_json JSONB NOT NULL
);

-- currency_data_processed
CREATE TABLE IF NOT EXISTS dim_currencies (
    currency_code VARCHAR(3) PRIMARY KEY, -- np. 'USD', 'EUR', 'PLN'
    currency_name VARCHAR(50) NOT NULL
);

-- raw_data_processed
CREATE TABLE IF NOT EXISTS dim_commodities (
    commodity_code VARCHAR(10) PRIMARY KEY, -- np. 'XCU' (Miedź), 'ALU' (Aluminium)
    commodity_name VARCHAR(100) NOT NULL,
    unit VARCHAR(20) NOT NULL -- np. 'per_tonne', 'per_ounce'
);

-- Dzienne ceny i kursy (Zunifikowane)
CREATE TABLE IF NOT EXISTS fct_daily_market_prices (
    id SERIAL PRIMARY KEY,
    price_date DATE NOT NULL,
    commodity_code VARCHAR(10) REFERENCES dim_commodities(commodity_code),
    currency_code VARCHAR(3) REFERENCES dim_currencies(currency_code),
    price_in_currency NUMERIC(12, 4) NOT NULL, -- Cena oryginalna z API
    price_pln NUMERIC(12, 4) NOT NULL,        -- Cena przeliczona na PLN przez ETL
    is_anomaly BOOLEAN DEFAULT FALSE,         -- Flaga anomalii (wyliczana w ETL)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_market_entry UNIQUE (price_date, commodity_code, currency_code)
);

-- Inicjalizacja podstawowych danych słownikowych (Wymiary)
INSERT INTO dim_currencies (currency_code, currency_name) VALUES
('USD', 'US Dollar'),
('EUR', 'Euro'),
('PLN', 'Polish Zloty')
ON CONFLICT (currency_code) DO NOTHING;

INSERT INTO dim_commodities (commodity_code, commodity_name, unit) VALUES
('XCU', 'Copper', 'tonne'),
('ALU', 'Aluminum', 'tonne'),
('XAU', 'Gold', 'ounce'),
('XAG', 'Silver', 'ounce')
ON CONFLICT (commodity_code) DO NOTHING;
DO 
$$
    BEGIN
        FOR i in 0..9 LOOP
            EXECUTE format('
                CREATE TABLE quote_history_%s IF NOT EXISTS (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(16) NOT NULL,
                    asset_type INTEGER NOT NULL DEFAULT 0,
                    date_day DATE NOT NULL,
                    quote JSONB NOT NULL,
                    update_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                );', i);
            EXECUTE format('COMMENT ON COLUMN quote_history_%s.code IS ''资产编码'';', i);
            EXECUTE format('COMMENT ON COLUMN quote_history_%s.asset_type IS ''资产类型 0股票/1基金'';', i);
            EXECUTE format('COMMENT ON COLUMN quote_history_%s.quote IS ''行情'';', i);
        END LOOP;
    END;
$$

CREATE TABLE IF NOT EXISTS asset_info(
    id SERIAL PRIMARY KEY,
    code VARCHAR(16) NOT NULL,
    asset_type INTEGER NOT NULL DEFAULT 0,
    asset_name VARCHAR(32) NOT NULL,
    create_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


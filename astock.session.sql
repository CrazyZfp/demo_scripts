DO 
$$
    BEGIN
        FOR i in 0..9 LOOP
            EXECUTE format('ALTER TABLE stock_history_%s RENAME TO quote_history_%s;', i, i );
            EXECUTE format('ALTER TABLE quote_history_%s 
                    ADD asset_type INTEGER NOT NULL DEFAULT 0,
                    ADD update_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;', i );
            EXECUTE format('COMMENT ON COLUMN quote_history_%s.code IS ''资产编码'';', i);
            EXECUTE format('COMMENT ON COLUMN quote_history_%s.asset_type IS ''资产类型 0股票/1基金'';', i);
            EXECUTE format('COMMENT ON COLUMN quote_history_%s.quote IS ''行情'';', i);
        END LOOP;
    END;
$$
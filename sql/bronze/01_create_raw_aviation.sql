
-- Aviation Data Intelligence v1.1
-- Tabela inicial de ingestao da camada Bronze

CREATE TABLE IF NOT EXISTS bronze.raw_aviation (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_aviation_ingested_at
    ON bronze.raw_aviation (ingested_at);

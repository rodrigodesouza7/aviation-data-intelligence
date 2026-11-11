
-- Aviation Data Intelligence v1.1
-- Camada Silver: estados das aeronaves

CREATE TABLE IF NOT EXISTS silver.aircraft_states (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    bronze_id BIGINT NOT NULL
        REFERENCES bronze.raw_aviation(id),

    icao24 VARCHAR(6) NOT NULL,
    callsign VARCHAR(20),
    origin_country VARCHAR(100),

    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    baro_altitude DOUBLE PRECISION,
    velocity DOUBLE PRECISION,

    observation_time TIMESTAMPTZ NOT NULL,

    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_aircraft_observation
        UNIQUE (bronze_id, icao24)
);

CREATE INDEX IF NOT EXISTS idx_aircraft_observation_time
    ON silver.aircraft_states (observation_time);

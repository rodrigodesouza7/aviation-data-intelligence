
-- Aviation Data Intelligence v1.1
-- Camada Gold: resumo operacional do tráfego aéreo

CREATE TABLE IF NOT EXISTS gold.air_traffic_summary (
    bronze_id BIGINT PRIMARY KEY
        REFERENCES bronze.raw_aviation(id),

    observation_time TIMESTAMPTZ NOT NULL,

    total_aircraft INTEGER NOT NULL,

    aircraft_with_position INTEGER NOT NULL,

    aircraft_with_altitude INTEGER NOT NULL,

    avg_altitude_m DOUBLE PRECISION,

    avg_velocity_ms DOUBLE PRECISION,

    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_total_aircraft
        CHECK (total_aircraft >= 0),

    CONSTRAINT chk_aircraft_with_position
        CHECK (
            aircraft_with_position >= 0
            AND aircraft_with_position <= total_aircraft
        ),

    CONSTRAINT chk_aircraft_with_altitude
        CHECK (
            aircraft_with_altitude >= 0
            AND aircraft_with_altitude <= total_aircraft
        )
);

CREATE INDEX IF NOT EXISTS idx_air_traffic_observation_time
    ON gold.air_traffic_summary (observation_time);

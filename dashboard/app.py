"""Dashboard analítico dos snapshots de tráfego aéreo."""

import pandas as pd
import streamlit as st
from sqlalchemy import text

from aviation.database.connection import get_engine
from aviation.quality import get_quality_query


st.set_page_config(
    page_title="Aviation Data Intelligence",
    page_icon="✈️",
    layout="wide",
)

st.title("Aviation Data Intelligence")
st.caption("Análise histórica de snapshots da OpenSky — não é monitoramento em tempo real.")


@st.cache_data(ttl=60)
def load_gold_data():
    """Consulta os indicadores consolidados na camada Gold."""
    engine = get_engine()
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        bronze_id,
                        observation_time,
                        total_aircraft,
                        aircraft_with_position,
                        aircraft_with_altitude,
                        avg_altitude_m,
                        avg_velocity_ms
                    FROM gold.air_traffic_summary
                    ORDER BY observation_time, bronze_id
                """)
            )
            return pd.DataFrame(result.fetchall(), columns=result.keys())
    finally:
        engine.dispose()


try:
    df = load_gold_data()
except Exception:
    st.error("Não foi possível consultar a camada Gold. Verifique o PostgreSQL e a configuração local.")
    st.stop()

if df.empty:
    st.info("Nenhum lote processado foi encontrado na camada Gold.")
    st.stop()

df["observation_time"] = pd.to_datetime(
    df["observation_time"], utc=True
)

latest = df.iloc[-1]

st.subheader("Último snapshot")

col1, col2, col3 = st.columns(3)
col1.metric("Aeronaves", int(latest["total_aircraft"]))
col2.metric("Com posição", int(latest["aircraft_with_position"]))
col3.metric("Com altitude", int(latest["aircraft_with_altitude"]))

col4, col5, col6 = st.columns(3)
col4.metric(
    "Altitude média",
    f'{latest["avg_altitude_m"]:,.0f} m'
    if pd.notna(latest["avg_altitude_m"]) else "N/D",
)
col5.metric(
    "Velocidade média",
    f'{latest["avg_velocity_ms"]:,.1f} m/s'
    if pd.notna(latest["avg_velocity_ms"]) else "N/D",
)
col6.metric("Lotes processados", len(df))

st.subheader("Comparação entre snapshots")
st.caption(
    "Cada grupo de barras representa um lote processado. "
    "Os dados não representam uma série temporal contínua."
)

chart_data = df.set_index(
    df["bronze_id"].map(lambda value: f"Lote {value}")
)[
    ["total_aircraft", "aircraft_with_position", "aircraft_with_altitude"]
]

st.bar_chart(chart_data, stack=False)

st.subheader("Histórico consolidado")
st.dataframe(
    df,
    width="stretch",
    hide_index=True,
)

st.subheader("Qualidade dos dados")
st.caption(
    "Comparação por lote entre estados recebidos na Bronze e registros carregados "
    "na Silver. Registros não carregados não são necessariamente inválidos; "
    "podem incluir duplicidades ou falhas de transformação."
)

@st.cache_data(ttl=60)
def load_quality_data():
    engine = get_engine()
    try:
        with engine.connect() as connection:
            result = connection.execute(get_quality_query())
            return pd.DataFrame(result.fetchall(), columns=result.keys())
    finally:
        engine.dispose()

try:
    quality = load_quality_data()
    if not quality.empty:
        q1, q2, q3 = st.columns(3)
        q1.metric("Estados recebidos", int(quality["received_count"].sum()))
        q2.metric("Registros na Silver", int(quality["accepted_count"].sum()))
        q3.metric("Não carregados", int(quality["not_loaded_count"].sum()))
        st.dataframe(quality, hide_index=True, width="stretch")
        st.caption(
            "Posição ausente e coordenadas fora do intervalo são indicadores "
            "diagnósticos; não significam rejeição automática no pipeline atual."
        )
except Exception:
    st.warning("Não foi possível carregar os indicadores de qualidade.")


"""Aviation Data Intelligence — Dashboard de inteligência operacional.

Analisa snapshots históricos da OpenSky para apoiar a avaliação
da atividade aeronáutica observada e da qualidade dos dados.

Não representa monitoramento em tempo real.
"""

import pandas as pd
import streamlit as st
from sqlalchemy import text

from aviation.database.connection import get_engine
from aviation.quality import get_quality_query


# ============================================================
# 1. CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Aviation Data Intelligence | Operational Analytics",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }

        div[data-testid="stMetric"] {
            background-color: rgba(128, 128, 128, 0.07);
            border: 1px solid rgba(128, 128, 128, 0.15);
            border-radius: 12px;
            padding: 16px;
        }

        div[data-testid="stMetricLabel"] {
            font-weight: 500;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 2. FUNÇÕES AUXILIARES
# ============================================================

def format_number(value, decimals=0):
    """Formata números para apresentação em português brasileiro."""
    if pd.isna(value):
        return "N/D"

    formatted = f"{float(value):,.{decimals}f}"

    return (
        formatted.replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )


def format_percent(numerator, denominator):
    """Calcula percentual, tratando denominadores inválidos."""
    if pd.isna(denominator) or denominator <= 0:
        return None

    return 100 * numerator / denominator


def format_delta(current, previous):
    """Calcula variação percentual entre dois snapshots."""
    if pd.isna(current) or pd.isna(previous) or previous <= 0:
        return None

    return 100 * (current - previous) / previous


def format_datetime(value):
    """Formata horário UTC de observação."""
    if pd.isna(value):
        return "N/D"

    return pd.Timestamp(value).strftime("%d/%m/%Y %H:%M UTC")


def dataframe_to_csv(dataframe):
    """Exporta dados em CSV compatível com planilhas brasileiras."""
    return dataframe.to_csv(
        index=False,
        sep=";",
        decimal=",",
    ).encode("utf-8-sig")


# ============================================================
# 3. CONSULTAS POSTGRESQL
# ============================================================

@st.cache_data(ttl=60)
def load_gold_data():
    """Carrega indicadores consolidados da camada Gold."""
    engine = get_engine()

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT
                        bronze_id,
                        observation_time,
                        total_aircraft,
                        aircraft_with_position,
                        aircraft_with_altitude,
                        avg_altitude_m,
                        avg_velocity_ms
                    FROM gold.air_traffic_summary
                    ORDER BY
                        observation_time ASC NULLS FIRST,
                        bronze_id ASC
                    """
                )
            )

            return pd.DataFrame(
                result.fetchall(),
                columns=result.keys(),
            )
    finally:
        engine.dispose()


@st.cache_data(ttl=60)
def load_quality_data():
    """Carrega indicadores de qualidade Bronze versus Silver."""
    engine = get_engine()

    try:
        with engine.connect() as connection:
            result = connection.execute(get_quality_query())

            return pd.DataFrame(
                result.fetchall(),
                columns=result.keys(),
            )
    finally:
        engine.dispose()


# ============================================================
# 4. CARREGAMENTO E PREPARAÇÃO
# ============================================================

st.title("Aviation Data Intelligence")

st.caption(
    "Operational Analytics | Inteligência operacional "
    "baseada em snapshots históricos da OpenSky"
)

st.info(
    "**Objetivo de negócio:** apoiar a análise da atividade "
    "aeronáutica observada e identificar limitações de "
    "qualidade e cobertura dos dados disponíveis."
)

try:
    gold = load_gold_data()

except Exception:
    st.error(
        "Não foi possível consultar a camada Gold. "
        "Verifique a conexão com o PostgreSQL."
    )
    st.stop()

if gold.empty:
    st.warning(
        "Nenhum snapshot processado foi encontrado "
        "na camada Gold."
    )
    st.stop()

gold["observation_time"] = pd.to_datetime(
    gold["observation_time"],
    utc=True,
    errors="coerce",
)

numeric_columns = [
    "total_aircraft",
    "aircraft_with_position",
    "aircraft_with_altitude",
    "avg_altitude_m",
    "avg_velocity_ms",
]

for column in numeric_columns:
    gold[column] = pd.to_numeric(
        gold[column],
        errors="coerce",
    )

gold = gold.sort_values(
    ["observation_time", "bronze_id"],
    na_position="first",
).reset_index(drop=True)

gold["position_coverage_pct"] = gold.apply(
    lambda row: format_percent(
        row["aircraft_with_position"],
        row["total_aircraft"],
    ),
    axis=1,
)

gold["altitude_coverage_pct"] = gold.apply(
    lambda row: format_percent(
        row["aircraft_with_altitude"],
        row["total_aircraft"],
    ),
    axis=1,
)


# ============================================================
# 5. FILTROS
# ============================================================

st.sidebar.header("Filtros de análise")

valid_dates = gold["observation_time"].dropna()

if valid_dates.empty:
    st.error(
        "Os snapshots não possuem datas de observação válidas."
    )
    st.stop()

min_date = valid_dates.min().date()
max_date = valid_dates.max().date()

selected_period = st.sidebar.date_input(
    "Período de observação (UTC)",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_period, (tuple, list)):
    if len(selected_period) != 2:
        st.info("Selecione as datas inicial e final.")
        st.stop()

    start_date, end_date = selected_period
else:
    start_date = end_date = selected_period

if start_date > end_date:
    st.warning(
        "A data inicial não pode ser posterior à data final."
    )
    st.stop()

filtered = gold.loc[
    gold["observation_time"].dt.date.between(
        start_date,
        end_date,
    )
].copy()

if filtered.empty:
    st.warning(
        "Não existem snapshots no período selecionado."
    )
    st.stop()

filtered = filtered.sort_values(
    ["observation_time", "bronze_id"]
).reset_index(drop=True)

st.sidebar.divider()

st.sidebar.markdown("**Fonte:** OpenSky Network")
st.sidebar.markdown("**Armazenamento:** PostgreSQL")
st.sidebar.markdown("**Arquitetura:** Bronze / Silver / Gold")
st.sidebar.markdown("**Orquestração:** Apache Airflow")

st.sidebar.caption(
    "Dados históricos coletados periodicamente. "
    "A cobertura depende da disponibilidade da fonte."
)


# ============================================================
# 6. CONTEXTO DA ANÁLISE
# ============================================================

latest = filtered.iloc[-1]

previous = (
    filtered.iloc[-2]
    if len(filtered) > 1
    else None
)

st.markdown(
    f"**Período analisado:** "
    f"{start_date.strftime('%d/%m/%Y')} até "
    f"{end_date.strftime('%d/%m/%Y')}"
)

st.caption(
    f"Última observação selecionada: "
    f"{format_datetime(latest['observation_time'])} "
    f"| Lote: {latest['bronze_id']}"
)

tab_executive, tab_quality, tab_exploration = st.tabs(
    [
        "Visão executiva",
        "Qualidade dos dados",
        "Exploração analítica",
    ]
)


# ============================================================
# 7. VISÃO EXECUTIVA
# ============================================================

with tab_executive:

    st.header("Panorama operacional")

    st.write(
        "Indicadores do snapshot mais recente dentro do "
        "período selecionado."
    )

    current_aircraft = latest["total_aircraft"]

    previous_aircraft = (
        previous["total_aircraft"]
        if previous is not None
        else None
    )

    aircraft_delta = (
        format_delta(
            current_aircraft,
            previous_aircraft,
        )
        if previous is not None
        else None
    )

    position_coverage = latest["position_coverage_pct"]
    altitude_coverage = latest["altitude_coverage_pct"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Aeronaves observadas",
        format_number(current_aircraft),
        delta=(
            f"{aircraft_delta:+.1f}%"
            if aircraft_delta is not None
            else None
        ),
        help=(
            "Total de estados de aeronaves no último "
            "snapshot. A variação compara duas coletas "
            "consecutivas do período filtrado."
        ),
    )

    col2.metric(
        "Cobertura de posição",
        (
            f"{format_number(position_coverage, 1)}%"
            if position_coverage is not None
            else "N/D"
        ),
        help=(
            "Aeronaves com posição divididas pelo "
            "total de aeronaves do snapshot."
        ),
    )

    col3.metric(
        "Cobertura de altitude",
        (
            f"{format_number(altitude_coverage, 1)}%"
            if altitude_coverage is not None
            else "N/D"
        ),
        help=(
            "Aeronaves com altitude divididas pelo "
            "total de aeronaves do snapshot."
        ),
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Altitude média",
        (
            f"{format_number(latest['avg_altitude_m'])} m"
            if pd.notna(latest["avg_altitude_m"])
            else "N/D"
        ),
    )

    col5.metric(
        "Velocidade média",
        (
            f"{format_number(latest['avg_velocity_ms'], 1)} m/s"
            if pd.notna(latest["avg_velocity_ms"])
            else "N/D"
        ),
    )

    col6.metric(
        "Snapshots analisados",
        format_number(len(filtered)),
    )

    st.divider()

    st.subheader("Evolução das observações")

    st.caption(
        "Comparação dos totais registrados em cada coleta. "
        "Os pontos representam snapshots discretos, "
        "não uma medição contínua do tráfego aéreo."
    )

    chart = filtered[
        [
            "observation_time",
            "bronze_id",
            "total_aircraft",
            "aircraft_with_position",
            "aircraft_with_altitude",
        ]
    ].copy()

    chart["snapshot"] = chart.apply(
        lambda row: (
            f"{format_datetime(row['observation_time'])}"
            f" | Lote {row['bronze_id']}"
        ),
        axis=1,
    )

    chart = chart.set_index("snapshot")[
        [
            "total_aircraft",
            "aircraft_with_position",
            "aircraft_with_altitude",
        ]
    ]

    chart = chart.rename(
        columns={
            "total_aircraft": "Aeronaves observadas",
            "aircraft_with_position": "Com posição",
            "aircraft_with_altitude": "Com altitude",
        }
    )

    st.line_chart(chart)

    st.divider()

    st.subheader("Interpretação operacional")

    if aircraft_delta is None:
        st.info(
            "Não há dois snapshots comparáveis com base "
            "positiva no período selecionado."
        )

    elif aircraft_delta > 0:
        st.info(
            f"O último snapshot apresentou aumento de "
            f"{format_number(aircraft_delta, 1)}% no número "
            f"de aeronaves observadas em relação à coleta anterior."
        )

    elif aircraft_delta < 0:
        st.info(
            f"O último snapshot apresentou redução de "
            f"{format_number(abs(aircraft_delta), 1)}% no número "
            f"de aeronaves observadas em relação à coleta anterior."
        )

    else:
        st.info(
            "O total de aeronaves observadas permaneceu "
            "igual ao da coleta anterior."
        )

    st.caption(
        "A variação observada não demonstra, isoladamente, "
        "crescimento ou queda do tráfego aéreo real. "
        "Diferenças de cobertura, horários e disponibilidade "
        "da OpenSky podem influenciar os resultados."
    )


# ============================================================
# 8. QUALIDADE DOS DADOS
# ============================================================

with tab_quality:

    st.header("Qualidade e confiabilidade dos dados")

    st.write(
        "Comparação entre estados recebidos na camada Bronze "
        "e registros persistidos na camada Silver."
    )

    try:
        quality = load_quality_data()

    except Exception:
        quality = pd.DataFrame()

        st.warning(
            "Não foi possível consultar os indicadores "
            "de qualidade dos dados."
        )

    if quality.empty:

        st.info(
            "Não existem indicadores de qualidade disponíveis."
        )

    else:

        quality = quality[
            quality["bronze_id"].isin(
                filtered["bronze_id"]
            )
        ].copy()

        if quality.empty:

            st.info(
                "Não existem indicadores de qualidade "
                "para o período selecionado."
            )

        else:

            received = int(
                quality["received_count"].sum()
            )

            accepted = int(
                quality["accepted_count"].sum()
            )

            not_loaded = int(
                quality["not_loaded_count"].sum()
            )

            load_rate = format_percent(
                accepted,
                received,
            )

            q1, q2, q3, q4 = st.columns(4)

            q1.metric(
                "Estados recebidos",
                format_number(received),
            )

            q2.metric(
                "Registros na Silver",
                format_number(accepted),
            )

            q3.metric(
                "Não carregados",
                format_number(not_loaded),
            )

            q4.metric(
                "Taxa de carregamento",
                (
                    f"{format_number(load_rate, 1)}%"
                    if load_rate is not None
                    else "N/D"
                ),
            )

            st.divider()

            st.subheader("Diagnóstico de qualidade")

            missing_position = int(
                quality["missing_position_count"].sum()
            )

            invalid_position = int(
                quality["invalid_position_count"].sum()
            )

            d1, d2 = st.columns(2)

            d1.metric(
                "Estados com posição ausente",
                format_number(missing_position),
            )

            d2.metric(
                "Estados com posição fora do intervalo",
                format_number(invalid_position),
            )

            st.caption(
                "Os indicadores de posição ausente e "
                "coordenadas fora do intervalo são diagnósticos. "
                "Não representam necessariamente registros "
                "rejeitados pelo pipeline."
            )

            st.subheader("Qualidade por lote")

            quality_display = quality.rename(
                columns={
                    "bronze_id": "Lote",
                    "received_count": "Recebidos",
                    "accepted_count": "Carregados",
                    "not_loaded_count": "Não carregados",
                    "missing_position_count": "Posição ausente",
                    "invalid_position_count": "Posição inválida",
                }
            )

            st.dataframe(
                quality_display,
                hide_index=True,
                width="stretch",
            )

            st.download_button(
                "Exportar indicadores de qualidade (CSV)",
                data=dataframe_to_csv(quality_display),
                file_name="aviation_data_quality.csv",
                mime="text/csv",
            )

            st.info(
                "**Interpretação:** registros não carregados "
                "podem decorrer de duplicidades, regras de "
                "transformação ou inconsistências. "
                "A diferença entre Bronze e Silver não "
                "deve ser interpretada automaticamente "
                "como erro de processamento."
            )


# ============================================================
# 9. EXPLORAÇÃO ANALÍTICA
# ============================================================

with tab_exploration:

    st.header("Exploração dos snapshots")

    st.write(
        "Consulte os indicadores históricos para investigar "
        "diferenças entre coletas e períodos."
    )

    e1, e2, e3 = st.columns(3)

    e1.metric(
        "Snapshots selecionados",
        format_number(len(filtered)),
    )

    e2.metric(
        "Média de aeronaves por snapshot",
        format_number(
            filtered["total_aircraft"].mean(),
            1,
        ),
    )

    e3.metric(
        "Máximo observado em um snapshot",
        format_number(
            filtered["total_aircraft"].max()
        ),
    )

    st.divider()

    st.subheader("Histórico consolidado")

    history = filtered[
        [
            "bronze_id",
            "observation_time",
            "total_aircraft",
            "aircraft_with_position",
            "aircraft_with_altitude",
            "avg_altitude_m",
            "avg_velocity_ms",
            "position_coverage_pct",
            "altitude_coverage_pct",
        ]
    ].copy()

    history["observation_time"] = history[
        "observation_time"
    ].dt.strftime("%d/%m/%Y %H:%M UTC")

    history = history.rename(
        columns={
            "bronze_id": "Lote",
            "observation_time": "Observação (UTC)",
            "total_aircraft": "Aeronaves",
            "aircraft_with_position": "Com posição",
            "aircraft_with_altitude": "Com altitude",
            "avg_altitude_m": "Altitude média (m)",
            "avg_velocity_ms": "Velocidade média (m/s)",
            "position_coverage_pct": "Cobertura posição (%)",
            "altitude_coverage_pct": "Cobertura altitude (%)",
        }
    )

    st.dataframe(
        history,
        hide_index=True,
        width="stretch",
    )

    st.download_button(
        "Exportar histórico (CSV)",
        data=dataframe_to_csv(history),
        file_name="aviation_historical_snapshots.csv",
        mime="text/csv",
    )

    st.divider()

    st.subheader("Limitações da análise")

    st.markdown(
        """
        - Cada linha representa um snapshot de observação.
        - Uma aeronave pode aparecer em vários snapshots.
        - A soma dos totais não representa aeronaves únicas.
        - Os intervalos de coleta podem variar.
        - A cobertura da OpenSky não é necessariamente completa.
        - O dashboard não monitora aeronaves em tempo real.
        - Os indicadores não permitem concluir congestionamento,
          atrasos ou capacidade aeroportuária.
        """
    )


# ============================================================
# 10. RODAPÉ
# ============================================================

st.divider()

st.caption(
    "Aviation Data Intelligence | Python • PostgreSQL • "
    "Apache Airflow • Streamlit | "
    "Projeto demonstrativo de Engenharia de Dados e "
    "Business Intelligence."
)


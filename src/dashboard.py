import pandas as pd
import streamlit as st

from services.temperature_service import (
    compare_locations_by_day,
    compare_periods,
    filter_by_location,
    filter_by_period,
    get_temperature_readings,
    initialize_database,
    make_month_options,
)


@st.cache_resource
def initialize_application() -> None:
    """Executa o preparo do banco uma vez por processo do Streamlit."""
    ingestion_result = initialize_database()

    # As consultas em cache só devem ser reaproveitadas após a carga inicial terminar.
    if ingestion_result and ingestion_result["inserted"]:
        st.cache_data.clear()


@st.cache_data
def load_temperature_table():
    """Carrega a série de leituras que alimenta os filtros e gráficos."""
    return get_temperature_readings()


def format_brazilian_date(value):
    """Formata datas para a exibição consistente nos gráficos."""
    return pd.to_datetime(value).strftime("%d-%m-%Y")


LOCATION_LABELS = {"In": "Dentro da sala", "Out": "Fora da sala"}


def main() -> None:
    st.set_page_config(page_title="Dashboard de Temperaturas IoT", layout="wide")
    st.title("Dashboard de Temperaturas IoT")

    # A inicialização fica fora do fluxo de interação para evitar DDL a cada filtro.
    initialize_application()

    temperature_df = load_temperature_table()
    if temperature_df.empty:
        st.warning("Nenhum dado encontrado no banco.")
        return

    min_date = temperature_df["noted_date"].min().date()
    max_date = temperature_df["noted_date"].max().date()

    # Os filtros laterais definem qual subconjunto alimenta os gráficos principais.
    st.sidebar.header("Filtros")
    location_options = [location for location in LOCATION_LABELS if location in temperature_df["out_in"].unique()]
    selected_locations = st.sidebar.multiselect(
        "Origem da leitura",
        location_options,
        default=location_options,
        format_func=lambda location: LOCATION_LABELS[location],
    )
    period_option = st.sidebar.selectbox(
        "Selecione o período",
        ["Ver tudo", "Último mês", "Última semana", "Um dia"],
        index=0,
    )
    selected_day = None
    if period_option == "Um dia":
        selected_day = st.sidebar.date_input("Dia específico", value=max_date, min_value=min_date, max_value=max_date)

    filtered_df = filter_by_location(temperature_df, selected_locations)
    filtered_df = filter_by_period(filtered_df, period_option, selected_day)

    if filtered_df.empty:
        st.warning("Nenhum dado disponível para o filtro selecionado.")
        return

    # A comparação é opcional e usa sempre a série completa para evitar filtros conflitantes.
    st.sidebar.markdown("---")
    st.sidebar.subheader("Comparar temperatura médias dos períodos")
    compare_enabled = st.sidebar.checkbox("Ativar comparação")

    comparison_result = None
    if compare_enabled:
        compare_mode = st.sidebar.selectbox(
            "Tipo de comparação",
            ["Comparar dois meses", "Comparar duas semanas", "Comparar dois dias"],
            index=0,
        )

        if compare_mode == "Comparar dois meses":
            month_options = make_month_options(temperature_df)
            if len(month_options) >= 2:
                month_a = st.sidebar.selectbox("Mês A", month_options, index=0)
                month_b = st.sidebar.selectbox("Mês B", month_options, index=len(month_options) - 1)
                comparison_result = compare_periods(temperature_df, compare_mode, month_a, month_b)
        elif compare_mode == "Comparar duas semanas":
            week_start_options = pd.date_range(start=min_date, end=max_date, freq="7D").date
            if len(week_start_options) >= 2:
                week_a = st.sidebar.selectbox("Início semana A", week_start_options, index=0)
                week_b = st.sidebar.selectbox("Início semana B", week_start_options, index=len(week_start_options) - 1)
                comparison_result = compare_periods(temperature_df, compare_mode, week_a, week_b)
        else:
            day_options = pd.date_range(start=min_date, end=max_date, freq="D").date
            if len(day_options) >= 2:
                day_a = st.sidebar.selectbox("Dia A", day_options, index=0)
                day_b = st.sidebar.selectbox("Dia B", day_options, index=len(day_options) - 1)
                comparison_result = compare_periods(temperature_df, compare_mode, day_a, day_b)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Dentro x fora da sala")
    location_comparison_enabled = st.sidebar.checkbox("Comparar em um dia")
    location_comparison_day = None
    if location_comparison_enabled:
        comparable_days = (
            temperature_df.assign(dia=temperature_df["noted_date"].dt.date)
            .groupby("dia")["out_in"]
            .nunique()
            .loc[lambda count: count >= 2]
            .index.tolist()
        )
        if comparable_days:
            default_day = max(comparable_days)
            selected_location_day = st.sidebar.date_input(
                "Dia para comparação",
                value=default_day,
                min_value=min(comparable_days),
                max_value=max(comparable_days),
            )
            if selected_location_day in comparable_days:
                location_comparison_day = selected_location_day
            else:
                st.sidebar.caption("Selecione um dia com leituras de dentro e fora da sala.")

    # Exibe a síntese e os gráficos separados somente quando os dois períodos possuem dados.
    if comparison_result:
        diff = comparison_result["diff"]
        if diff > 0:
            comparison_text = f"{comparison_result['period_a_label']} ficou {diff:.2f}°C mais quente que {comparison_result['period_b_label']}."
        elif diff < 0:
            comparison_text = f"{comparison_result['period_b_label']} ficou {abs(diff):.2f}°C mais quente que {comparison_result['period_a_label']}."
        else:
            comparison_text = f"As médias foram iguais em {comparison_result['period_a_label']} e {comparison_result['period_b_label']}"

        st.subheader("Comparação entre períodos")
        st.info(comparison_text)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"### {comparison_result['period_a_label']}")
            st.metric("Média do período A", f"{comparison_result['avg_a']:.2f}°C")
            a_daily = comparison_result["period_a_df"].assign(dia=comparison_result["period_a_df"]["noted_date"].dt.date).groupby("dia", as_index=False)["temp"].mean()
            if not a_daily.empty:
                a_daily["dia"] = a_daily["dia"].apply(format_brazilian_date)
                st.line_chart(a_daily.set_index("dia")["temp"].rename("Temperatura média"))
        with col_b:
            st.markdown(f"### {comparison_result['period_b_label']}")
            st.metric("Média do período B", f"{comparison_result['avg_b']:.2f}°C")
            b_daily = comparison_result["period_b_df"].assign(dia=comparison_result["period_b_df"]["noted_date"].dt.date).groupby("dia", as_index=False)["temp"].mean()
            if not b_daily.empty:
                b_daily["dia"] = b_daily["dia"].apply(format_brazilian_date)
                st.line_chart(b_daily.set_index("dia")["temp"].rename("Temperatura média"))

    # A visão intradiária só faz sentido quando o usuário seleciona um dia específico.
    if period_option == "Um dia":
        st.subheader(f"Resumo do dia {selected_day.strftime('%d-%m-%Y')}")
        col_min, col_max, col_avg = st.columns(3)
        with col_min:
            st.metric("Mínima do dia", f"{filtered_df['temp'].min():.2f}°C")
        with col_max:
            st.metric("Máxima do dia", f"{filtered_df['temp'].max():.2f}°C")
        with col_avg:
            st.metric("Média do dia", f"{filtered_df['temp'].mean():.2f}°C")

        st.subheader("Temperatura ao longo do dia")
        hourly = filtered_df.copy()
        hourly["hora"] = hourly["noted_date"].dt.strftime("%H:%M")
        hourly = hourly.groupby("hora", as_index=False)["temp"].mean()
        if not hourly.empty:
            st.line_chart(hourly.set_index("hora")["temp"].rename("Temperatura (°C)"))
        else:
            st.warning("Nenhuma leitura registrada para este dia.")

    if location_comparison_enabled and location_comparison_day:
        comparison_day = compare_locations_by_day(temperature_df, location_comparison_day)
        if comparison_day is None:
            st.info("Não há dados suficientes para comparar dentro e fora da sala neste dia.")
        else:
            inside_avg = comparison_day["inside_avg"]
            outside_avg = comparison_day["outside_avg"]
            st.subheader(f"Comparação dentro x fora — {comparison_day['day'].strftime('%d-%m-%Y')}")

            inside_col, outside_col, difference_col = st.columns(3)
            inside_col.metric(
                "Média dentro da sala",
                f"{inside_avg:.2f}°C" if pd.notna(inside_avg) else "Sem dados",
            )
            outside_col.metric(
                "Média fora da sala",
                f"{outside_avg:.2f}°C" if pd.notna(outside_avg) else "Sem dados",
            )
            difference_col.metric(
                "Diferença (fora − dentro)",
                f"{comparison_day['diff']:.2f}°C" if pd.notna(comparison_day['diff']) else "Sem dados",
            )

            day_readings = temperature_df[temperature_df["noted_date"].dt.date == comparison_day["day"]].copy()
            hourly_location = (
                day_readings.assign(hora=day_readings["noted_date"].dt.strftime("%H:%M"))
                .groupby(["hora", "out_in"], as_index=False)["temp"]
                .mean()
                .pivot(index="hora", columns="out_in", values="temp")
                .rename(columns=LOCATION_LABELS)
            )
            if not hourly_location.empty:
                st.line_chart(hourly_location.rename_axis(None, axis="columns"))
            else:
                st.warning("Nenhuma série horária disponível para esse dia.")

    # Agregações derivadas do período filtrado para os indicadores gerais do dashboard.
    temp_media_por_dia = filtered_df.assign(dia=filtered_df["noted_date"].dt.date).groupby("dia", as_index=False)["temp"].mean().rename(columns={"dia": "Dia", "temp": "Média da temperatura"})
    leituras_por_dia = filtered_df.assign(dia=filtered_df["noted_date"].dt.date).groupby("dia", as_index=False).size().rename(columns={"size": "Quantidade de leituras", "dia": "Dia"})

    st.subheader("Média de temperatura por dia")
    if not temp_media_por_dia.empty:
        temp_media_por_dia = temp_media_por_dia.sort_values("Dia").copy()
        temp_media_por_dia["Dia"] = temp_media_por_dia["Dia"].apply(format_brazilian_date)
        st.line_chart(temp_media_por_dia.set_index("Dia")["Média da temperatura"])
    else:
        st.warning("Nenhuma média de temperatura por dia disponível.")

    temp_max_min_por_dia = filtered_df.assign(dia=filtered_df["noted_date"].dt.date).groupby("dia", as_index=False).agg(
        temp_max=("temp", "max"),
        temp_min=("temp", "min"),
    ).rename(columns={"dia": "Dia"})

    st.subheader("Temperatura máxima e mínima por dia")
    if not temp_max_min_por_dia.empty:
        temp_max_min_por_dia = temp_max_min_por_dia.sort_values("Dia").copy()
        temp_max_min_por_dia["Dia"] = temp_max_min_por_dia["Dia"].apply(format_brazilian_date)
        st.line_chart(temp_max_min_por_dia.set_index("Dia")[["temp_max", "temp_min"]])
    else:
        st.warning("Nenhuma temperatura máxima e mínima por dia disponível.")

    st.subheader("Quantidades de leituras por dia")
    if not leituras_por_dia.empty:
        leituras_por_dia = leituras_por_dia.sort_values("Dia").copy()
        leituras_por_dia["Dia"] = leituras_por_dia["Dia"].apply(format_brazilian_date)
        st.bar_chart(leituras_por_dia.set_index("Dia")["Quantidade de leituras"])
    else:
        st.warning("Nenhuma quantidade de leituras por dia disponível.")


if __name__ == "__main__":
    main()

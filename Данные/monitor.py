from __future__ import annotations

from datetime import date

import streamlit as st

from src.cbr_metals import fetch_metal
from src.cbr_fx import fetch_fx, load_currency_catalog, DEFAULT_CURRENCIES
from src.charts import make_price_chart
from src.cpp_signals import render_cpp_summary_section, render_cpp_full_section


st.set_page_config(page_title="CBR Monitor", layout="wide")
st.title("Мониторинг ЦБ РФ")


def order_codes_popular_first(all_codes: list[str], popular_codes: list[str]) -> list[str]:
    popular = [c for c in popular_codes if c in all_codes]
    others = [c for c in all_codes if c not in popular]
    return popular + others


with st.sidebar:
    st.header("Фильтры")

    start = st.date_input("Начало", value=date(2020, 1, 1))
    end = st.date_input("Конец", value=date.today())
    granularity = st.radio("Гранулярность", ["День", "Неделя", "Месяц"], horizontal=True, index=0)

    signal_n = st.number_input(
        "Период анализа n (дней)",
        min_value=2,
        max_value=365,
        value=20,
        step=1,
        help="За сколько последних дней C++-модуль считает среднюю цену и сигнал.",
    )

    view_mode = st.radio("Показать", ["Цена", "Доходность (%)"], horizontal=True, key="view_mode")
    normalize = st.checkbox("Нормировать (100 в начале)", value=False, key="normalize")
    log_scale = st.checkbox("Логарифмическая шкала", value=False, key="log_scale")

    refresh = st.button("Обновить данные сейчас (очистить кэш)")

    step = st.selectbox(
        "Показывать точки",
        [1, 2, 3, 5, 7],
        index=0,
        format_func=lambda x: "каждый день" if x == 1 else f"каждый {x}-й день",
    )


if start > end:
    st.error("Начальная дата не может быть позже конечной.")
    st.stop()

date_from = start.strftime("%d/%m/%Y")
date_to = end.strftime("%d/%m/%Y")


@st.cache_data(ttl=60 * 60)
def load_metals(d1: str, d2: str):
    return fetch_metal(d1, d2)


@st.cache_data(ttl=60 * 60)
def load_fx(d1: str, d2: str, codes: tuple[str, ...]):
    return fetch_fx(d1, d2, list(codes))


if refresh:
    load_metals.clear()
    load_fx.clear()
    st.sidebar.success("Кэш очищен, данные будут загружены заново.")
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()


tab_metals, tab_fx = st.tabs(["Драгметаллы", "Валюты (курс рубля)"])


with tab_metals:
    st.subheader("Драгметаллы (ЦБ РФ) — руб/г")

    with st.spinner("Загружаю данные драгметаллов ЦБ РФ..."):
        metals_daily = load_metals(date_from, date_to)

    metals_daily = metals_daily.sort_index()
    metals_daily.index.name = "date"

    if metals_daily.empty:
        st.warning("Данные по металлам не пришли. Попробуй другой период.")
        st.stop()

    metals = list(metals_daily.columns)
    selected = st.multiselect("Металлы", metals, default=metals, key="metals")

    if not selected:
        st.info("Выбери хотя бы один металл.")
        st.stop()

    render_cpp_summary_section(
        wide_daily=metals_daily,
        selected=selected,
        n=int(signal_n),
        title=f"Сводка C++ по металлам (n = {signal_n})",
        empty_message="Недостаточно данных для расчёта сводки по металлам.",
        decimals=2,
    )

    metals_view = metals_daily[selected].copy()

    if granularity == "Неделя":
        metals_view = metals_view.resample("W").last()
    elif granularity == "Месяц":
        metals_view = metals_view.resample("M").last()

    if step > 1:
        metals_view = metals_view.iloc[::step]

    if view_mode == "Доходность (%)":
        data = metals_view.pct_change() * 100.0
        data = data.dropna()
        y_label = "%"
        title = "Доходность драгметаллов, %"
    else:
        data = metals_view
        y_label = "руб/г"
        title = "Цены драгметаллов (руб/г)"
        if normalize:
            first_row = data.dropna().iloc[0]
            data = data / first_row * 100.0
            y_label = "индекс (100 = начало)"

    fig = make_price_chart(data, title=title, y_title=y_label, series_name="metal")
    if view_mode == "Цена" and log_scale and not normalize:
        fig.update_yaxes(type="log")
    st.plotly_chart(fig, width="stretch")

    render_cpp_full_section(
        wide_daily=metals_daily,
        selected=selected,
        n=int(signal_n),
        title=f"Полная таблица сигналов по металлам (n = {signal_n})",
        empty_message="Недостаточно данных для расчёта полной таблицы по металлам.",
        decimals=2,
    )


with tab_fx:
    st.subheader("Валюты (ЦБ РФ)")

    with st.spinner("Загружаю справочник валют..."):
        catalog = load_currency_catalog()

    if catalog.empty:
        st.warning("Не удалось загрузить справочник валют.")
        st.stop()

    popular_codes = [c for c in DEFAULT_CURRENCIES if c in catalog.index]
    all_codes_catalog = catalog.index.tolist()
    all_codes = order_codes_popular_first(all_codes_catalog, popular_codes)
    default_codes = popular_codes

    col_a, col_b = st.columns([2, 1])
    with col_a:
        fx_selected = st.multiselect(
            "Валюты",
            options=all_codes,
            default=default_codes,
            format_func=lambda c: f"{c} — {catalog.loc[c, 'name']}",
            key="fx_codes",
        )
    with col_b:
        fx_quote = st.radio(
            "Вид котировки",
            ["RUB за 1 валюту", "Валюты за 1 RUB"],
            index=0,
            key="fx_quote",
        )

    if not fx_selected:
        st.info("Выбери хотя бы одну валюту.")
        st.stop()

    with st.spinner("Загружаю курсы валют ЦБ РФ..."):
        fx_daily = load_fx(date_from, date_to, tuple(fx_selected))

    fx_daily = fx_daily.sort_index()
    fx_daily.index.name = "date"

    if fx_daily.empty:
        st.warning("Данные по валютам не пришли. Попробуй другой период.")
        st.stop()

    if fx_quote == "Валюты за 1 RUB":
        fx_daily = 1.0 / fx_daily

    fx_available = [c for c in fx_selected if c in fx_daily.columns]
    missing = [c for c in fx_selected if c not in fx_daily.columns]

    if missing:
        st.warning("Не получилось загрузить данные для: " + ", ".join(missing))

    if not fx_available:
        st.stop()

    render_cpp_summary_section(
        wide_daily=fx_daily,
        selected=fx_available,
        n=int(signal_n),
        title=f"Сводка C++ по валютам (n = {signal_n})",
        empty_message="Недостаточно данных для расчёта сводки по валютам.",
        decimals=4,
    )

    fx_view = fx_daily[fx_available].copy()

    if granularity == "Неделя":
        fx_view = fx_view.resample("W").last()
    elif granularity == "Месяц":
        fx_view = fx_view.resample("M").last()

    if step > 1:
        fx_view = fx_view.iloc[::step]

    if view_mode == "Доходность (%)":
        data_fx = fx_view.pct_change() * 100.0
        data_fx = data_fx.dropna()
        y_label = "%"
        title = "Доходность валют, %"
    else:
        data_fx = fx_view
        y_label = "руб" if fx_quote == "RUB за 1 валюту" else "валюта"
        title = "Курсы валют (ЦБ РФ)"
        if normalize:
            first_row = data_fx.dropna().iloc[0]
            data_fx = data_fx / first_row * 100.0
            y_label = "индекс (100 = начало)"

    fig = make_price_chart(data_fx, title=title, y_title=y_label, series_name="ccy")
    if view_mode == "Цена" and log_scale and not normalize:
        fig.update_yaxes(type="log")
    st.plotly_chart(fig, width="stretch")

    render_cpp_full_section(
        wide_daily=fx_daily,
        selected=fx_available,
        n=int(signal_n),
        title=f"Полная таблица сигналов по валютам (n = {signal_n})",
        empty_message="Недостаточно данных для расчёта полной таблицы по валютам.",
        decimals=4,
    )
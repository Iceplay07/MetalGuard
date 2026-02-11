from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd
import streamlit as st

from src.cbr_metals import fetch_metal
from src.cbr_fx import fetch_fx, load_currency_catalog, DEFAULT_CURRENCIES
from src.charts import make_price_chart


st.set_page_config(page_title="CBR Monitor", layout="wide")
st.title("Мониторинг ЦБ РФ")


# -------------------------
# Helpers
# -------------------------

def _fmt_num(x: float | int | None, decimals: int = 2) -> str:
    if x is None:
        return "—"
    if isinstance(x, float) and pd.isna(x):
        return "—"
    try:
        return f"{float(x):,.{decimals}f}".replace(",", " ")
    except Exception:
        return "—"


def _delta_str(abs_change: float | None, pct_change: float | None, decimals: int = 2) -> str:
    if abs_change is None or (isinstance(abs_change, float) and pd.isna(abs_change)):
        return "—"
    abs_s = f"{abs_change:+,.{decimals}f}".replace(",", " ")
    if pct_change is None or (isinstance(pct_change, float) and pd.isna(pct_change)):
        return abs_s
    return f"{abs_s} ({pct_change:+.2f}%)"


def _asof_value(s: pd.Series, target: pd.Timestamp) -> tuple[pd.Timestamp | None, float | None]:
    """Последнее доступное значение на дату <= target."""
    ss = s.dropna()
    if ss.empty:
        return None, None
    ss = ss.loc[:target]
    if ss.empty:
        return None, None
    d = ss.index[-1]
    v = float(ss.iloc[-1])
    return d, v


def make_last_change_table(
    wide_daily: pd.DataFrame,
    selected: Iterable[str],
    decimals: int,
    horizons_days: dict[str, int] | None = None,
) -> pd.DataFrame:
    """Строит таблицу:
    - Последнее значение
    - Изменения за 1д/1н/1м: абсолют + %
    - Даты сравнения (as-of)
    """
    horizons_days = horizons_days or {"1д": 1, "1н": 7, "1м": 30}

    cols = [c for c in selected if c in wide_daily.columns]
    if not cols:
        return pd.DataFrame()

    df = wide_daily[cols].sort_index().copy()
    if df.dropna(how="all").empty:
        return pd.DataFrame()

    out_rows: list[dict] = []

    for name in cols:
        s = df[name].dropna()
        if s.empty:
            continue

        last_d = s.index.max()
        last_v = float(s.loc[last_d])

        row: dict = {
            "Инструмент": name,
            "Дата": last_d.date().isoformat(),
            "Последнее": _fmt_num(last_v, decimals),
        }

        for label, days in horizons_days.items():
            target = last_d - pd.Timedelta(days=days)
            prev_d, prev_v = _asof_value(s, target)
            if prev_d is None or prev_v is None:
                row[f"Δ {label}"] = "—"
                row[f"с {label}"] = "—"
            else:
                abs_ch = last_v - prev_v
                pct_ch = (last_v / prev_v - 1.0) * 100.0 if prev_v != 0 else None
                row[f"Δ {label}"] = _delta_str(abs_ch, pct_ch, decimals)
                row[f"с {label}"] = prev_d.date().isoformat()

        out_rows.append(row)

    if not out_rows:
        return pd.DataFrame()

    out = pd.DataFrame(out_rows).set_index("Инструмент")

    col_order = ["Дата", "Последнее"]
    for k in horizons_days.keys():
        col_order += [f"Δ {k}", f"с {k}"]
    out = out.reindex(columns=[c for c in col_order if c in out.columns])
    return out


def order_codes_popular_first(all_codes: list[str], popular_codes: list[str]) -> list[str]:
    """Возвращает список кодов: популярные сверху, остальные дальше (в исходном порядке all_codes)."""
    popular = [c for c in popular_codes if c in all_codes]
    others = [c for c in all_codes if c not in popular]
    return popular + others


# -------------------------
# Sidebar filters
# -------------------------

with st.sidebar:
    st.header("Фильтры")

    start = st.date_input("Начало", value=date(2020, 1, 1))
    end = st.date_input("Конец", value=date.today())
    granularity = st.radio("Гранулярность", ["День", "Неделя", "Месяц"], horizontal=True, index=0)

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
def load_metals(d1: str, d2: str) -> pd.DataFrame:
    return fetch_metal(d1, d2)


@st.cache_data(ttl=60 * 60)
def load_fx(d1: str, d2: str, codes: tuple[str, ...]) -> pd.DataFrame:
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


# -------------------------
# Tab: Metals
# -------------------------

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

    st.subheader("Последняя цена и изменения")
    summary_metals = make_last_change_table(metals_daily, selected, decimals=2)
    st.dataframe(summary_metals, width="stretch")
    st.caption(
        "Δ 1д/1н/1м считаются от последней доступной даты назад по календарю; "
        "если дата выпадает на выходной/праздник — берётся ближайшая предыдущая запись."
    )

    # Данные для графика
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

    st.subheader("Последние значения (как на графике)")
    st.dataframe(data.tail(20), width="stretch")


# -------------------------
# Tab: FX
# -------------------------

with tab_fx:
    st.subheader("Курсы валют (ЦБ РФ)")
    st.caption("По умолчанию: **рублей за 1 единицу валюты**. Можно переключить на обратный курс (валюты за 1 RUB).")

    with st.spinner("Загружаю справочник валют..."):
        catalog = load_currency_catalog(d=0)

    if catalog.empty:
        st.warning("Не удалось загрузить справочник валют. Проверь доступ к cbr.ru")
        st.stop()

    # --- популярные сверху ---
    popular_codes = [c for c in DEFAULT_CURRENCIES if c in catalog.index]
    all_codes_catalog = catalog.index.tolist()  # весь справочник
    all_codes = order_codes_popular_first(all_codes_catalog, popular_codes)
    default_codes = popular_codes  # по умолчанию выделяем популярные

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

    # Переключение котировки
    if fx_quote == "Валюты за 1 RUB":
        fx_daily = 1.0 / fx_daily

    st.subheader("Последний курс и изменения")
    fx_available = [c for c in fx_selected if c in fx_daily.columns]
    missing = [c for c in fx_selected if c not in fx_daily.columns]
    if missing:
        st.warning("Не получилось загрузить данные для: " + ", ".join(missing))
    if not fx_available:
        st.stop()

    summary_fx = make_last_change_table(fx_daily, fx_available, decimals=4)
    st.dataframe(summary_fx, width="stretch")
    st.caption(
        "Δ 1д/1н/1м считаются от последней доступной даты назад по календарю; "
        "если дата выпадает на выходной/праздник — берётся ближайшая предыдущая запись."
    )

    # Данные для графика
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

    st.subheader("Последние значения (как на графике)")
    st.dataframe(data_fx.tail(20), width="stretch")

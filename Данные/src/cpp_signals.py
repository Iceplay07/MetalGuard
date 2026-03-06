from __future__ import annotations

from typing import Iterable

import pandas as pd
import streamlit as st

from src.cpp_bridge import analyze_series


def _fmt_num(x: float | int | None, decimals: int = 2) -> str:
    if x is None:
        return "—"
    try:
        xf = float(x)
    except Exception:
        return "—"
    if pd.isna(xf):
        return "—"
    return f"{xf:,.{decimals}f}".replace(",", " ")


def _fmt_delta(abs_change: float | None, pct_change: float | None, decimals: int = 2) -> str:
    if abs_change is None:
        return "—"
    try:
        av = float(abs_change)
    except Exception:
        return "—"
    if pd.isna(av):
        return "—"

    abs_s = f"{av:+,.{decimals}f}".replace(",", " ")

    if pct_change is None:
        return abs_s
    try:
        pv = float(pct_change)
    except Exception:
        return abs_s
    if pd.isna(pv):
        return abs_s

    return f"{abs_s} ({pv:+.2f}%)"


def _date_str(x) -> str:
    try:
        return pd.Timestamp(x).date().isoformat()
    except Exception:
        return str(x)


def _one_day_percent(series: pd.Series) -> float | None:
    s = series.dropna()
    if len(s) < 2:
        return None

    prev = float(s.iloc[-2])
    curr = float(s.iloc[-1])

    if prev == 0:
        return None

    return ((curr / prev) - 1.0) * 100.0


def collect_cpp_analysis(
    wide_daily: pd.DataFrame,
    selected: Iterable[str],
    n: int,
) -> pd.DataFrame:
    rows: list[dict] = []

    cols = [c for c in selected if c in wide_daily.columns]
    if not cols:
        return pd.DataFrame()

    for name in cols:
        s = wide_daily[name].dropna()
        if s.empty:
            continue

        last_date = s.index[-1]
        last_value = float(s.iloc[-1])
        prices = s.astype(float).tolist()

        try:
            r = analyze_series(prices, n=n)
            rows.append(
                {
                    "Инструмент": name,
                    "Дата": _date_str(last_date),
                    "Последнее": r["price_today"],
                    "Δ 1д abs": r["change_price_1d"],
                    "Δ 1д %": _one_day_percent(s),
                    "Средняя 7д": r["average_7d"],
                    "Δ 7д abs": r["change_av_7d"],
                    "Δ 7д %": r["change_7d_per"],
                    "Средняя 30д": r["average_30d"],
                    "Δ 30д abs": r["change_av_30d"],
                    "Δ 30д %": r["change_30d_per"],
                    f"Средняя {n}д": r["average_nd"],
                    f"Δ {n}д abs": r["change_av_nd"],
                    f"Δ {n}д %": r["change_nd_per"],
                    "Сигнал": r["signal"],
                }
            )
        except Exception as e:
            rows.append(
                {
                    "Инструмент": name,
                    "Дата": _date_str(last_date),
                    "Последнее": last_value,
                    "Δ 1д abs": None,
                    "Δ 1д %": None,
                    "Средняя 7д": None,
                    "Δ 7д abs": None,
                    "Δ 7д %": None,
                    "Средняя 30д": None,
                    "Δ 30д abs": None,
                    "Δ 30д %": None,
                    f"Средняя {n}д": None,
                    f"Δ {n}д abs": None,
                    f"Δ {n}д %": None,
                    "Сигнал": f"Ошибка: {e}",
                }
            )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def make_cpp_summary_table(raw_df: pd.DataFrame, n: int, decimals: int = 2) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for _, row in raw_df.iterrows():
        rows.append(
            {
                "Инструмент": row["Инструмент"],
                "Дата": row["Дата"],
                "Последнее": _fmt_num(row["Последнее"], decimals),
                "Δ 1д": _fmt_delta(row["Δ 1д abs"], row["Δ 1д %"], decimals),
                "Δ 7д от средней": _fmt_delta(row["Δ 7д abs"], row["Δ 7д %"], decimals),
                "Δ 30д от средней": _fmt_delta(row["Δ 30д abs"], row["Δ 30д %"], decimals),
                f"Δ {n}д от средней": _fmt_delta(row[f"Δ {n}д abs"], row[f"Δ {n}д %"], decimals),
            }
        )

    return pd.DataFrame(rows)


def make_cpp_full_table(raw_df: pd.DataFrame, n: int, decimals: int = 2) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for _, row in raw_df.iterrows():
        rows.append(
            {
                "Инструмент": row["Инструмент"],
                "Дата": row["Дата"],
                "Последнее": _fmt_num(row["Последнее"], decimals),
                "Δ 1д": _fmt_delta(row["Δ 1д abs"], row["Δ 1д %"], decimals),
                "Средняя 7д": _fmt_num(row["Средняя 7д"], decimals),
                "Δ 7д от средней": _fmt_delta(row["Δ 7д abs"], row["Δ 7д %"], decimals),
                "Средняя 30д": _fmt_num(row["Средняя 30д"], decimals),
                "Δ 30д от средней": _fmt_delta(row["Δ 30д abs"], row["Δ 30д %"], decimals),
                f"Средняя {n}д": _fmt_num(row[f"Средняя {n}д"], decimals),
                f"Δ {n}д от средней": _fmt_delta(row[f"Δ {n}д abs"], row[f"Δ {n}д %"], decimals),
                "Сигнал": row["Сигнал"],
            }
        )

    return pd.DataFrame(rows)


def render_cpp_summary_section(
    wide_daily: pd.DataFrame,
    selected: Iterable[str],
    n: int,
    title: str,
    empty_message: str,
    decimals: int = 2,
) -> None:
    st.subheader(title)

    raw_df = collect_cpp_analysis(wide_daily, selected, n=n)
    summary_df = make_cpp_summary_table(raw_df, n=n, decimals=decimals)

    if summary_df.empty:
        st.info(empty_message)
        return

    st.table(summary_df)


def render_cpp_full_section(
    wide_daily: pd.DataFrame,
    selected: Iterable[str],
    n: int,
    title: str,
    empty_message: str,
    decimals: int = 2,
) -> None:
    st.subheader(title)

    raw_df = collect_cpp_analysis(wide_daily, selected, n=n)
    full_df = make_cpp_full_table(raw_df, n=n, decimals=decimals)

    if full_df.empty:
        st.info(empty_message)
        return

    st.table(full_df)

    st.markdown("**Как формируется сигнал**")
    st.caption(
        f"Сигнал строится по логике C++-модуля. "
        f"BUY ставится, когда актив заметно ниже своей средней за 7 и 30 дней, "
        f"и за последний день появился рост — это трактуется как возможный отскок вверх. "
        f"SELL ставится, когда актив заметно выше средней за 7 и 30 дней, "
        f"и за последний день появилось снижение — это трактуется как ослабление после роста. "
        f"Период {n} дней используется как дополнительный долгий контекст, "
        f"но не как единственный триггер. Если условия не дают уверенного перевеса, выводится HOLD."
    )
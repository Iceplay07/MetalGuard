from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from src.backend.cbr_metals import fetch_metal
from src.backend.cbr_fx import fetch_fx
from src.frontend.mobile_view import render_mobile_app
from src.frontend.desktop_view import render_desktop_app


def is_mobile_device() -> bool:
    try:
        headers = st.context.headers
        ua = str(headers.get("User-Agent", "")).lower()
    except Exception:
        ua = ""

    mobile_markers = [
        "iphone",
        "android",
        "mobile",
        "ipad",
        "opera mini",
        "windows phone",
    ]
    return any(marker in ua for marker in mobile_markers)


def apply_quick_range():
    today = date.today()
    value = st.session_state.quick_range

    if value == "1 неделя":
        st.session_state.start_date = today - timedelta(days=7)
        st.session_state.end_date = today
    elif value == "1 месяц":
        st.session_state.start_date = today - timedelta(days=40)
        st.session_state.end_date = today
    elif value == "3 месяца":
        st.session_state.start_date = today - timedelta(days=90)
        st.session_state.end_date = today
    elif value == "1 год":
        st.session_state.start_date = today - timedelta(days=365)
        st.session_state.end_date = today
    else:
        st.session_state.start_date = date(2020, 1, 1)
        st.session_state.end_date = today


@st.cache_data(ttl=60 * 60)
def load_metals(d1: str, d2: str):
    return fetch_metal(d1, d2)


@st.cache_data(ttl=60 * 60)
def load_fx(d1: str, d2: str, codes: tuple[str, ...]):
    return fetch_fx(d1, d2, list(codes))


mobile = is_mobile_device()

st.set_page_config(
    page_title="CBR Monitor",
    layout="centered" if mobile else "wide",
)

st.title("Мониторинг ЦБ РФ")

today = date.today()

if "start_date" not in st.session_state:
    st.session_state.start_date = today - timedelta(days=40)

if "end_date" not in st.session_state:
    st.session_state.end_date = today

if "quick_range" not in st.session_state:
    st.session_state.quick_range = "30 дней"

common_kwargs = {
    "load_metals": load_metals,
    "load_fx": load_fx,
    "apply_quick_range": apply_quick_range,
}

if mobile:
    render_mobile_app(**common_kwargs)
else:
    render_desktop_app(**common_kwargs)
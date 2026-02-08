from datetime import date
import streamlit as st

from src.cbr_metals import fetch_metal
from src.charts import make_price_chart


st.set_page_config(page_title="Metals Monitor", layout="wide")
st.title("Драгметаллы (ЦБ РФ) — интерактивный мониторинг (руб/г)")

# --- Фильтры слева ---
with st.sidebar:
    st.header("Фильтры")

    start = st.date_input("Начало", value=date(2020, 1, 1))
    end = st.date_input("Конец", value=date.today())
    granularity = st.radio("Гранулярность", ["День", "Неделя", "Месяц"], horizontal=True, index=0)

    view_mode = st.radio("Показать", ["Цена", "Доходность (%)"], horizontal=True)
    normalize = st.checkbox("Нормировать (100 в начале)", value=False)
    log_scale = st.checkbox("Логарифмическая шкала", value=False)
    refresh = st.button("Обновить данные сейчас (очистить кэш)")
    step = st.selectbox("Показывать точки", [1, 2, 3, 5, 7], index=0,
                        format_func=lambda x: "каждый день" if x == 1 else f"каждый {x}-й день")




if start > end:
    st.error("Начальная дата не может быть позже конечной.")
    st.stop()

date_from = start.strftime("%d/%m/%Y")
date_to = end.strftime("%d/%m/%Y")

@st.cache_data(ttl=60 * 60)
def load_prices(d1: str, d2: str):
    return fetch_metal(d1, d2)


if refresh:
    load_prices.clear()  # очистить кэш
    st.sidebar.success("Кэш очищен, данные будут загружены заново.")
    # перезапуск приложения, чтобы сразу увидеть обновление
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()


with st.spinner("Загружаю данные ЦБ РФ..."):
    prices = load_prices(date_from, date_to)

prices = prices.sort_index()
prices.index.name = "date"

if granularity == "Неделя":
    prices = prices.resample("W").last()   # последняя цена недели
elif granularity == "Месяц":
    prices = prices.resample("ME").last()   # последняя цена месяца


if prices.empty:
    st.warning("Данные не пришли. Попробуй другой период.")
    st.stop()


# --- Выбор металлов (после загрузки данных) ---
with st.sidebar:
    metals = list(prices.columns)
    selected = st.multiselect("Металлы", metals, default=metals)

if not selected:
    st.info("Выбери хотя бы один металл слева.")
    st.stop()

data = prices[selected].copy()


# Прореживание: каждый N-й день
if step > 1:
    data = data.iloc[::step]

if view_mode == "Доходность (%)":
    # дневная доходность в процентах
    data = data.pct_change() * 100.0
    data = data.dropna()
    y_label = "%"
    title = "Дневная доходность драгметаллов, % (наведите, чтобы увидеть значения)"
else:
    y_label = "руб/г"
    title = "Цены драгметаллов (наведите, чтобы увидеть точные значения)"

    # Нормировка имеет смысл только для цен
    if normalize:
        # защита: если первая строка содержит NaN, берём первую непустую
        first_row = data.dropna().iloc[0]
        data = data / first_row * 100.0
        y_label = "индекс (100 = начало)"



fig = make_price_chart(data, title=title, y_title=y_label)

# лог-шкала — только для цен (не для доходностей и не для индексного режима)
if view_mode == "Цена" and log_scale and not normalize:
    fig.update_yaxes(type="log")

st.plotly_chart(fig, width="stretch")

# =========================
# Таблица + маленькая сводка
# =========================
st.subheader("Сводка")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Начало", start.strftime("%Y-%m-%d"))
with col2:
    st.metric("Конец", end.strftime("%Y-%m-%d"))
with col3:
    st.metric("Точек", str(len(data)))


st.subheader("Последние значения")
st.dataframe(data.tail(20), width="stretch")

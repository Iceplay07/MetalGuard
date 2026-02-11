import functools
import xml.etree.ElementTree as ET

import pandas as pd
import requests


# Документация ЦБ РФ по XML-сервисам:
# https://www.cbr.ru/development/sxml/

CBR_VAL_LIST_URL = "https://www.cbr.ru/scripts/XML_valFull.asp"
CBR_DYNAMIC_URL = "https://www.cbr.ru/scripts/XML_dynamic.asp"


# Хороший стартовый набор валют (можно расширять выбором в интерфейсе)
DEFAULT_CURRENCIES = [
    "USD",  # доллар США
    "EUR",  # евро
    "CNY",  # юань
    "GBP",  # фунт стерлингов
    "JPY",  # иена
    "CHF",  # швейцарский франк
    "TRY",  # турецкая лира
    "KZT",  # тенге
]


def _safe_float(text: str | None) -> float | None:
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def _safe_int(text: str | None) -> int | None:
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


@functools.lru_cache(maxsize=4)
def load_currency_catalog(d: int = 0) -> pd.DataFrame:
    """Справочник валют ЦБ РФ.

    Возвращает DataFrame с индексом CharCode (USD/EUR/...),
    колонками: id, name, nominal.

    d=0 — валюты, устанавливаемые ежедневно (обычно то, что нужно).
    d=1 — устанавливаемые ежемесячно.
    """
    url = f"{CBR_VAL_LIST_URL}?d={d}"
    resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    rows: list[dict] = []
    # В XML_valFull.asp элементы обычно выглядят как <Item ID="R01235">...</Item>
    for item in root.findall(".//Item"):
        attrs = {k.lower(): v for k, v in (item.attrib or {}).items()}
        item_id = attrs.get("id")

        payload = {child.tag: (child.text or "").strip() for child in list(item)}
        char_code = (
            payload.get("CharCode")
            or payload.get("ISO_Char_Code")
            or payload.get("ISOCharCode")
            or payload.get("ISOChar_Code")
        )
        name = payload.get("Name") or payload.get("EngName") or payload.get("ParentCode")
        nominal = _safe_int(payload.get("Nominal"))

        if not item_id or not char_code:
            continue
        rows.append(
            {
                "char_code": char_code.strip().upper(),
                "id": item_id.strip(),
                "name": (name or "").strip(),
                "nominal": nominal,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["id", "name", "nominal"]).set_index(pd.Index([], name="char_code"))

    df = pd.DataFrame(rows)
    # На всякий случай оставим первую запись для каждого кода
    df = df.drop_duplicates(subset=["char_code"], keep="first").set_index("char_code").sort_index()
    return df


def fetch_fx(date_from: str, date_to: str, char_codes: list[str], d: int = 0) -> pd.DataFrame:
    """Скачивает динамику курсов валют ЦБ РФ за период.

    Параметры:
        date_from/date_to: строки в формате 'DD/MM/YYYY'
        char_codes: ['USD', 'EUR', ...]
        d: справочник валют (0 — дневные, 1 — месячные)

    Возвращает:
        wide DataFrame: index=date (datetime), columns=CharCode, values=руб за 1 единицу валюты (float)
    """
    catalog = load_currency_catalog(d=d)
    codes = [c.strip().upper() for c in char_codes if c and c.strip()]
    codes = [c for c in codes if c in catalog.index]
    if not codes:
        return pd.DataFrame()

    series_list: list[pd.Series] = []

    for code in codes:
        val_id = str(catalog.loc[code, "id"])
        url = f"{CBR_DYNAMIC_URL}?date_req1={date_from}&date_req2={date_to}&VAL_NM_RQ={val_id}"
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        rows = []
        for rec in root.findall(".//Record"):
            d_attr = rec.attrib.get("Date")
            value = _safe_float(rec.findtext("Value"))
            nominal = _safe_int(rec.findtext("Nominal"))
            if not d_attr or value is None:
                continue
            if not nominal:
                nominal = 1
            rows.append(
                {
                    "date": pd.to_datetime(d_attr, dayfirst=True, errors="coerce"),
                    "rub_per_1": value / float(nominal),
                }
            )

        if not rows:
            continue

        df = pd.DataFrame(rows).dropna(subset=["date"]).sort_values("date")
        s = df.set_index("date")["rub_per_1"].rename(code)
        series_list.append(s)

    if not series_list:
        return pd.DataFrame()
    wide = pd.concat(series_list, axis=1).sort_index()
    wide.index.name = "date"
    return wide


if __name__ == "__main__":
    df = fetch_fx("01/01/2024", "07/02/2026", ["USD", "EUR", "CNY"])
    print(df.tail())

import xml.etree.ElementTree as ET
import pandas as pd
import requests


CODE_METAL = {
    "1": "Gold (Au)",
    "2": "Silver (Ag)",
    "3": "Platinum (Pt)",
    "4": "Palladium (Pd)"
}

CBR_URL = "https://www.cbr.ru/scripts/xml_metall.asp"


def fetch_metal(date_from : str, date_to : str):
    """
        Скачивает цены ЦБ РФ по 4 металлам за период.

        Параметры:
            date_from/date_to: строки в формате 'DD/MM/YYYY'

        Возвращает:
            wide DataFrame: index=date (datetime), columns=металлы, values=руб/г (float)
        """
    url = f"{CBR_URL}?date_req1={date_from}&date_req2={date_to}"

    resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    rows = []
    for row in root.findall("Record"):
        d = row.attrib.get("Date")
        code = row.attrib.get("Code")
        buy = row.findtext("Buy")

        if not d or not code or not buy:
            continue
        if code not in CODE_METAL:
            continue

        try:
            price = float(buy.replace(",", "."))
        except ValueError:
            continue

        rows.append(
            {
                "date": pd.to_datetime(d, dayfirst=True, errors="coerce"),
                "metal": CODE_METAL[code],
                "rub_per_g": price,
            }
        )

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).dropna(subset=["date"])

    wide = (
        df.pivot_table(
            index="date",
            columns="metal",
            values="rub_per_g",
            aggfunc="last",
        )
        .sort_index()
    )


    col_order = [CODE_METAL[str(i)] for i in range(1, 5)]
    wide = wide.reindex(columns=[c for c in col_order if c in wide.columns])

    return wide

if __name__ == "__main__":
    df = fetch_metal("01/01/2024", "07/02/2026")
    print(df.tail())
    print(df.columns)

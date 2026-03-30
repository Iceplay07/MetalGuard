import pandas as pd
import plotly.express as px


def make_price_chart(
    wide: pd.DataFrame,
    title: str = "График",
    y_title: str = "",
    series_name: str = "series",
):
    df_long = (
        wide.reset_index()
        .melt(id_vars="date", var_name=series_name, value_name="value")
        .dropna()
    )

    fig = px.line(df_long, x="date", y="value", color=series_name, title=title)

    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Дата",
        yaxis_title=None if not y_title else y_title,
    )

    return fig
import pandas as pd
import plotly.express as px

def make_price_chart(wide: pd.DataFrame, title: str = "Металлы (руб/г)", y_title: str = "руб.г"):
    """
    wide: DataFrame с индексом date и колонками-металлами
    """
    df_long = (
        wide.reset_index()
        .melt(id_vars="date", var_name="metal", value_name="value")
        .dropna()
    )

    fig = px.line(df_long, x="date", y="value", color="metal", title=title)
    fig.update_layout(hovermode="x unified", xaxis_title="Дата", yaxis_title=y_title)
    return fig

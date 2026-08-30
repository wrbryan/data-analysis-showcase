from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import Input, Output

from components.callback_common import empty_figure
from components.layout import has_columns


def register_overview_callbacks(app, df: pd.DataFrame) -> None:
    yearly = None
    sports = None

    if has_columns(df, ["Year"]):
        yearly = (
            df.groupby("Year")
            .size()
            .reset_index(name="Entries")
            .sort_values("Year")
        )

    if has_columns(df, ["Sport"]):
        sports = (
            df.groupby("Sport")
            .size()
            .reset_index(name="Entries")
            .sort_values("Entries", ascending=False)
            .head(15)
        )

    @app.callback(
        Output("overview-events-by-year", "figure"),
        Output("overview-top-sports", "figure"),
        Input("overview-events-by-year", "id"),
    )
    def update_overview(_: str):
        if yearly is not None:
            fig_year = px.line(
                yearly,
                x="Year",
                y="Entries",
                title="Olympic Entries by Year",
            )
        else:
            fig_year = empty_figure("Year column not found")

        if sports is not None:
            fig_sport = px.bar(sports, x="Sport", y="Entries", title="Top Sports")
            fig_sport.update_layout(xaxis_tickangle=-35)
        else:
            fig_sport = empty_figure("Sport column not found")

        return fig_year, fig_sport

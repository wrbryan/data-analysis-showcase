from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import Input, Output

from components.callback_common import empty_figure
from components.layout import has_columns


def register_medals_callbacks(app, df: pd.DataFrame) -> None:
    medal_base_df = None
    if has_columns(df, ["Medal", "NOC", "Year"]):
        medal_base_df = df[df["Medal"].notna()].copy()

    @app.callback(
        Output("medals-by-country", "figure"),
        Output("medals-by-year", "figure"),
        Input("analysis-tabs", "value"),
        Input("medals-year-range", "value"),
        Input("medals-medal-type", "value"),
        Input("medals-season", "value"),
        Input("medals-top-n", "value"),
    )
    def update_medals(
        active_tab: str,
        year_range: list[int],
        medal_type: str,
        season_value: str,
        top_n: int,
    ):
        if active_tab != "medals":
            return (
                empty_figure("Open Medals tab to load chart"),
                empty_figure("Open Medals tab to load chart"),
            )

        if medal_base_df is None:
            return (
                empty_figure("Required medal columns not found"),
                empty_figure("Required medal columns not found"),
            )

        medal_df = medal_base_df
        medal_df = medal_df[
            (medal_df["Year"] >= year_range[0]) & (medal_df["Year"] <= year_range[1])
        ]

        if medal_type != "ALL":
            medal_df = medal_df[medal_df["Medal"] == medal_type]
        if season_value != "ALL" and "Season" in medal_df.columns:
            medal_df = medal_df[medal_df["Season"] == season_value]

        if medal_df.empty:
            return (
                empty_figure("No medals in selected slicer state"),
                empty_figure("No medals in selected slicer state"),
            )

        country_counts = (
            medal_df.groupby("NOC")
            .size()
            .reset_index(name="Medals")
            .sort_values("Medals", ascending=False)
            .head(top_n)
        )
        country_fig = px.bar(
            country_counts,
            x="NOC",
            y="Medals",
            title=f"Top {top_n} Countries by Medals",
        )

        year_medals = (
            medal_df.groupby(["Year", "Medal"])
            .size()
            .reset_index(name="Count")
            .sort_values("Year")
        )
        year_fig = px.bar(
            year_medals,
            x="Year",
            y="Count",
            color="Medal",
            category_orders={"Medal": ["Gold", "Silver", "Bronze"]},
            title="Medals by Year and Type",
        )

        return country_fig, year_fig

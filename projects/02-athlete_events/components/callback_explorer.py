from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import Input, Output

from components.callback_common import empty_figure

SCATTER_MAX_POINTS = 3000
BOX_MAX_CATEGORIES = 12
MAX_COLOR_LEVELS = 40
MAX_COLOR_LEVELS_HEAVY = 12


def register_explorer_callbacks(app, df: pd.DataFrame) -> None:
    @app.callback(
        Output("explorer-main-chart", "figure"),
        Input("analysis-tabs", "value"),
        Input("explorer-chart-type", "value"),
        Input("explorer-x-column", "value"),
        Input("explorer-y-column", "value"),
        Input("explorer-color-column", "value"),
    )
    def update_explorer(
        active_tab: str,
        chart_type: str,
        x_col: str,
        y_col: str | None,
        color_col: str,
    ):
        if active_tab != "explorer":
            return empty_figure("Open Explorer tab to load chart")

        if x_col not in df.columns:
            return empty_figure("Selected X column is not available")

        selected_color = color_col if color_col else None
        if selected_color and selected_color in df.columns:
            color_levels = int(df[selected_color].nunique(dropna=True))
            if color_levels > MAX_COLOR_LEVELS:
                # High-cardinality color fields (for example Name, ID) can hang or fail rendering.
                selected_color = None

        # Limit color splits for heavy chart types to avoid producing hundreds of traces.
        if chart_type in {"box", "bar", "bar_sum", "bar_avg"} and selected_color:
            heavy_color_levels = int(df[selected_color].nunique(dropna=True))
            if heavy_color_levels > MAX_COLOR_LEVELS_HEAVY:
                selected_color = None

        try:
            if chart_type == "histogram":
                if df[x_col].dropna().empty:
                    return empty_figure("Selected X column has no values")
                return px.histogram(
                    df,
                    x=x_col,
                    color=selected_color,
                    title=f"Histogram of {x_col}",
                )

            if chart_type == "bar":
                if y_col is not None:
                    if y_col not in df.columns:
                        return empty_figure("Selected Y column is not available")
                    if not pd.api.types.is_numeric_dtype(df[y_col]):
                        return empty_figure("Y column must be numeric for bar charts")

                    bar_df = df[[x_col, y_col] + ([selected_color] if selected_color else [])].copy()
                    bar_df = bar_df.dropna(subset=[x_col, y_col])
                    if bar_df.empty:
                        return empty_figure("No valid rows for selected bar columns")

                    bar_df["_x_bucket"] = bar_df[x_col].astype(str)
                    top_categories = bar_df["_x_bucket"].value_counts().head(30).index
                    bar_df = bar_df[bar_df["_x_bucket"].isin(top_categories)]

                    group_cols = ["_x_bucket"] + ([selected_color] if selected_color else [])
                    summary = (
                        bar_df.groupby(group_cols, dropna=False)[y_col]
                        .mean()
                        .reset_index(name="value")
                        .sort_values("value", ascending=False)
                    )

                    return px.bar(
                        summary,
                        x="_x_bucket",
                        y="value",
                        color=selected_color,
                        title=f"Average {y_col} by {x_col}",
                        labels={"_x_bucket": x_col, "value": f"Average {y_col}"},
                    )

                counts = (
                    df[x_col]
                    .astype(str)
                    .fillna("<NA>")
                    .to_frame(name="category")
                    .groupby("category", dropna=False)
                    .size()
                    .reset_index(name="count")
                    .sort_values("count", ascending=False)
                    .head(30)
                )
                return px.bar(
                    counts,
                    x="category",
                    y="count",
                    title=f"Top Values for {x_col}",
                    labels={"category": x_col, "count": "Count"},
                )

            if chart_type in {"bar_sum", "bar_avg"}:
                if y_col is None:
                    return empty_figure("Select a Y column for aggregated bar charts")
                if y_col not in df.columns:
                    return empty_figure("Selected Y column is not available")
                if not pd.api.types.is_numeric_dtype(df[y_col]):
                    return empty_figure("Y column must be numeric for aggregated bar charts")

                bar_df = df[[x_col, y_col] + ([selected_color] if selected_color else [])].copy()
                bar_df = bar_df.dropna(subset=[x_col, y_col])
                if bar_df.empty:
                    return empty_figure("No valid rows for selected bar columns")

                bar_df["_x_bucket"] = bar_df[x_col].astype(str)
                top_categories = bar_df["_x_bucket"].value_counts().head(30).index
                bar_df = bar_df[bar_df["_x_bucket"].isin(top_categories)]

                group_cols = ["_x_bucket"] + ([selected_color] if selected_color else [])
                agg_name = "sum" if chart_type == "bar_sum" else "mean"
                agg_label = "Sum" if chart_type == "bar_sum" else "Average"
                summary = (
                    bar_df.groupby(group_cols, dropna=False)[y_col]
                    .agg(agg_name)
                    .reset_index(name="value")
                    .sort_values("value", ascending=False)
                )

                return px.bar(
                    summary,
                    x="_x_bucket",
                    y="value",
                    color=selected_color,
                    title=f"{agg_label} {y_col} by {x_col}",
                    labels={"_x_bucket": x_col, "value": f"{agg_label} {y_col}"},
                )

            if chart_type == "scatter":
                if y_col is None:
                    return empty_figure("Select a Y column for scatter plots")
                if y_col not in df.columns:
                    return empty_figure("Selected Y column is not available")
                if not pd.api.types.is_numeric_dtype(df[y_col]):
                    return empty_figure("Y column must be numeric for scatter plots")

                scatter_df = df[[x_col, y_col] + ([selected_color] if selected_color else [])].copy()
                scatter_df = scatter_df.dropna(subset=[x_col, y_col])
                if scatter_df.empty:
                    return empty_figure("No valid points for selected scatter columns")
                if len(scatter_df) > SCATTER_MAX_POINTS:
                    scatter_df = scatter_df.sample(n=SCATTER_MAX_POINTS, random_state=42)

                return px.scatter(
                    scatter_df,
                    x=x_col,
                    y=y_col,
                    color=selected_color,
                    render_mode="webgl",
                    title=f"{y_col} vs {x_col}",
                )

            if chart_type != "box":
                return empty_figure("Unknown chart type selected")

            if y_col is None:
                return empty_figure("Select a Y column for box plots")
            if y_col not in df.columns:
                return empty_figure("Selected Y column is not available")
            if not pd.api.types.is_numeric_dtype(df[y_col]):
                return empty_figure("Y column must be numeric for box plots")

            box_df = df[[x_col, y_col] + ([selected_color] if selected_color else [])].copy()
            box_df = box_df.dropna(subset=[x_col, y_col])
            if box_df.empty:
                return empty_figure("No valid rows for selected box columns")

            x_as_str = box_df[x_col].astype(str)
            top_categories = x_as_str.value_counts().head(BOX_MAX_CATEGORIES).index
            box_df = box_df[x_as_str.isin(top_categories)].copy()
            if box_df.empty:
                return empty_figure("No valid rows in top categories for selected box columns")
            box_df["_x_bucket"] = box_df[x_col].astype(str)

            return px.box(
                box_df,
                x="_x_bucket",
                y=y_col,
                color=selected_color,
                points=False,
                title=f"Box Plot: {y_col} by {x_col}",
                labels={"_x_bucket": x_col},
            )
        except Exception as exc:
            return empty_figure(f"Could not render {chart_type} for current selection: {exc}")

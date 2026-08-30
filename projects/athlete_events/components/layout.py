from __future__ import annotations

from pathlib import Path
from typing import Iterable

import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table, dcc, html


def has_columns(df: pd.DataFrame, cols: Iterable[str]) -> bool:
    return all(col in df.columns for col in cols)


def kpi_cards(df: pd.DataFrame) -> dbc.Row:
    athlete_count = df["Name"].nunique() if "Name" in df.columns else len(df)
    team_count = df["Team"].nunique() if "Team" in df.columns else 0
    medal_count = df["Medal"].notna().sum() if "Medal" in df.columns else 0

    return dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6("Rows", className="card-subtitle text-muted"),
                            html.H3(f"{len(df):,}", className="mb-0"),
                        ]
                    )
                ),
                md=3,
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6("Unique Athletes", className="card-subtitle text-muted"),
                            html.H3(f"{athlete_count:,}", className="mb-0"),
                        ]
                    )
                ),
                md=3,
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6("Teams", className="card-subtitle text-muted"),
                            html.H3(f"{team_count:,}", className="mb-0"),
                        ]
                    )
                ),
                md=3,
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6("Medals", className="card-subtitle text-muted"),
                            html.H3(f"{medal_count:,}", className="mb-0"),
                        ]
                    )
                ),
                md=3,
            ),
        ],
        className="mb-4",
    )


def overview_container(df: pd.DataFrame) -> dbc.Container:
    return dbc.Container(
        [
            kpi_cards(df),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="overview-events-by-year"), md=6),
                    dbc.Col(dcc.Graph(id="overview-top-sports"), md=6),
                ]
            ),
        ],
        fluid=True,
    )


def demographics_container(df: pd.DataFrame) -> dbc.Container:
    sex_options = [{"label": "All", "value": "ALL"}]
    if "Sex" in df.columns:
        sex_values = sorted(df["Sex"].dropna().astype(str).unique().tolist())
        sex_options.extend({"label": sex, "value": sex} for sex in sex_values)

    season_options = [{"label": "All", "value": "ALL"}]
    if "Season" in df.columns:
        season_values = sorted(df["Season"].dropna().astype(str).unique().tolist())
        season_options.extend({"label": season, "value": season} for season in season_values)

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Sex"),
                            dcc.Dropdown(
                                id="demographics-sex",
                                options=sex_options,
                                value="ALL",
                                clearable=False,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Label("Season"),
                            dcc.Dropdown(
                                id="demographics-season",
                                options=season_options,
                                value="ALL",
                                clearable=False,
                            ),
                        ],
                        md=3,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="demographics-age-distribution"), md=6),
                    dbc.Col(dcc.Graph(id="demographics-height-weight"), md=6),
                ]
            ),
        ],
        fluid=True,
    )


def medals_container(df: pd.DataFrame) -> dbc.Container:
    year_min = int(df["Year"].min()) if "Year" in df.columns else 1896
    year_max = int(df["Year"].max()) if "Year" in df.columns else 2016
    season_options = [{"label": "All", "value": "ALL"}]
    if "Season" in df.columns:
        seasons = sorted(df["Season"].dropna().astype(str).unique().tolist())
        season_options.extend({"label": season, "value": season} for season in seasons)

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Year Range"),
                            dcc.RangeSlider(
                                id="medals-year-range",
                                min=year_min,
                                max=year_max,
                                value=[year_min, year_max],
                                step=1,
                                marks={year_min: str(year_min), year_max: str(year_max)},
                                updatemode="mouseup",
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Medal Type"),
                            dcc.Dropdown(
                                id="medals-medal-type",
                                options=[
                                    {"label": "All", "value": "ALL"},
                                    {"label": "Gold", "value": "Gold"},
                                    {"label": "Silver", "value": "Silver"},
                                    {"label": "Bronze", "value": "Bronze"},
                                ],
                                value="ALL",
                                clearable=False,
                            ),
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.Label("Season"),
                            dcc.Dropdown(
                                id="medals-season",
                                options=season_options,
                                value="ALL",
                                clearable=False,
                            ),
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.Label("Top N Countries"),
                            dcc.Dropdown(
                                id="medals-top-n",
                                options=[
                                    {"label": "10", "value": 10},
                                    {"label": "20", "value": 20},
                                    {"label": "30", "value": 30},
                                ],
                                value=20,
                                clearable=False,
                            ),
                        ],
                        md=2,
                    ),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="medals-by-country"), md=6),
                    dbc.Col(dcc.Graph(id="medals-by-year"), md=6),
                ]
            ),
        ],
        fluid=True,
    )


def explorer_container(df: pd.DataFrame) -> dbc.Container:
    explorer_columns = [col for col in df.columns if col != "ID"]
    numeric_columns = [col for col in explorer_columns if pd.api.types.is_numeric_dtype(df[col])]
    categorical_columns = [col for col in explorer_columns if col not in numeric_columns]
    max_color_levels = 12
    color_columns = [
        col
        for col in explorer_columns
        if int(df[col].nunique(dropna=True)) <= max_color_levels
    ]

    x_default = numeric_columns[0] if numeric_columns else explorer_columns[0]
    y_default = (
        numeric_columns[1]
        if len(numeric_columns) > 1
        else (numeric_columns[0] if numeric_columns else None)
    )
    color_default = categorical_columns[0] if categorical_columns and categorical_columns[0] in color_columns else ""

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("X column"),
                            dcc.Dropdown(
                                id="explorer-x-column",
                                options=[{"label": c, "value": c} for c in explorer_columns],
                                value=x_default,
                                clearable=False,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Label("Y column"),
                            dcc.Dropdown(
                                id="explorer-y-column",
                                options=[{"label": c, "value": c} for c in numeric_columns],
                                value=y_default,
                                clearable=True,
                                placeholder="Optional for histogram/bar",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Label("Color column"),
                            dcc.Dropdown(
                                id="explorer-color-column",
                                options=[{"label": "None", "value": ""}] + [{"label": c, "value": c} for c in color_columns],
                                value=color_default,
                                clearable=False,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Label("Chart type"),
                            dcc.Dropdown(
                                id="explorer-chart-type",
                                options=[
                                    {"label": "Histogram (counts)", "value": "histogram"},
                                    {"label": "Bar (auto: avg Y or counts)", "value": "bar"},
                                    {"label": "Bar (sum of Y)", "value": "bar_sum"},
                                    {"label": "Bar (average of Y)", "value": "bar_avg"},
                                    {"label": "Scatter", "value": "scatter"},
                                    {"label": "Box", "value": "box"},
                                ],
                                value="histogram",
                                clearable=False,
                            ),
                        ],
                        md=3,
                    ),
                ],
                className="mb-4",
            ),
            dcc.Graph(id="explorer-main-chart"),
            html.H4("Data Preview", className="mt-4"),
            dash_table.DataTable(
                data=df[explorer_columns].head(20).to_dict("records"),
                columns=[{"name": c, "id": c} for c in explorer_columns],
                page_size=10,
                style_table={"overflowX": "auto"},
                style_cell={
                    "fontFamily": "monospace",
                    "fontSize": 12,
                    "textAlign": "left",
                },
            ),
        ],
        fluid=True,
    )


def build_layout(df: pd.DataFrame, title: str, csv_path: str) -> dbc.Container:
    return dbc.Container(
        [
            html.H1(title, className="mt-4 mb-1 dashboard-title"),
            html.P(f"Source CSV: {Path(csv_path).name}", className="text-muted"),
            dcc.Tabs(
                id="analysis-tabs",
                value="overview",
                children=[
                    dcc.Tab(
                        label="Overview",
                        value="overview",
                        children=[overview_container(df)],
                    ),
                    dcc.Tab(
                        label="Demographics",
                        value="demographics",
                        children=[demographics_container(df)],
                    ),
                    dcc.Tab(
                        label="Medals",
                        value="medals",
                        children=[medals_container(df)],
                    ),
                    dcc.Tab(
                        label="Explorer",
                        value="explorer",
                        children=[explorer_container(df)],
                    ),
                ],
                className="mb-4",
            ),
        ],
        fluid=True,
        className="main-shell",
    )

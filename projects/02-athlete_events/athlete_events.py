from __future__ import annotations

import argparse
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from dash import Dash

from components.callbacks import register_callbacks
from components.layout import build_layout


TRANSPARENT_TEMPLATE_NAME = "athlete_events_transparent"


def configure_plotly_template() -> None:
    custom_template = go.layout.Template(pio.templates["plotly_white"])
    custom_template.layout.paper_bgcolor = "#ffffff"
    custom_template.layout.plot_bgcolor = "#ffffff"
    custom_template.layout.legend.bgcolor = "rgba(255,255,255,0.92)"
    pio.templates[TRANSPARENT_TEMPLATE_NAME] = custom_template
    pio.templates.default = TRANSPARENT_TEMPLATE_NAME


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the athlete events dashboard with modular components."
    )
    parser.add_argument(
        "--csv",
        default="athlete_events.csv",
        help="Path to the CSV file to load. Defaults to athlete_events.csv",
    )
    parser.add_argument(
        "--title",
        default="Athlete Events Dashboard",
        help="Dashboard title shown in the app header.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port for the Dash app. Defaults to 8050.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable Dash debug mode. Off by default for stability/performance.",
    )
    return parser.parse_args()


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    category_columns = [
        "Sex",
        "Team",
        "NOC",
        "Games",
        "Season",
        "City",
        "Sport",
        "Event",
        "Medal",
    ]
    for col in category_columns:
        if col in df.columns and df[col].dtype == "object":
            df[col] = df[col].astype("category")

    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")

    return df


def load_csv(path: str) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists() or not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Coerce numeric-like object columns while preserving text-heavy columns.
    for col in df.columns:
        if df[col].dtype == "object":
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().sum() >= int(0.9 * max(len(df), 1)):
                df[col] = converted

    return optimize_dtypes(df)


def build_app(df: pd.DataFrame, title: str, csv_path: str) -> Dash:
    assets_dir = Path(__file__).resolve().parent / "assets"
    configure_plotly_template()
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.FLATLY],
        assets_folder=str(assets_dir),
    )
    app.config.suppress_callback_exceptions = True

    # Layout comes from components folder.
    app.layout = build_layout(df, title, csv_path)
    # Callback registration comes from components folder.
    register_callbacks(app, df)

    return app


def main() -> None:
    args = parse_args()
    print(f"Loading CSV from {args.csv}...", flush=True)
    df = load_csv(args.csv)
    print(f"Loaded {len(df):,} rows. Building dashboard...", flush=True)
    app = build_app(df, args.title, args.csv)
    print(f"Starting Dash on http://127.0.0.1:{args.port}", flush=True)
    app.run(debug=args.debug, port=args.port)


if __name__ == "__main__":
    main()

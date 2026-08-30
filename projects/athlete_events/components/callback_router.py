from __future__ import annotations

import pandas as pd
from dash import Input, Output

from components.layout import (
    demographics_container,
    explorer_container,
    medals_container,
    overview_container,
)


def register_router_callback(app, df: pd.DataFrame) -> None:
    @app.callback(
        Output("analysis-view-container", "children"),
        Input("analysis-tabs", "value"),
    )
    def render_tab(tab_value: str):
        tab_to_container = {
            "overview": overview_container,
            "demographics": demographics_container,
            "medals": medals_container,
            "explorer": explorer_container,
        }
        selected_container = tab_to_container.get(tab_value, overview_container)
        return selected_container(df)

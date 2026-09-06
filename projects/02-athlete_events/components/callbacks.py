from __future__ import annotations

import pandas as pd

from components.callback_demographics import register_demographics_callbacks
from components.callback_explorer import register_explorer_callbacks
from components.callback_medals import register_medals_callbacks
from components.callback_overview import register_overview_callbacks


def register_callbacks(app, df: pd.DataFrame) -> None:
    register_overview_callbacks(app, df)
    register_demographics_callbacks(app, df)
    register_medals_callbacks(app, df)
    register_explorer_callbacks(app, df)

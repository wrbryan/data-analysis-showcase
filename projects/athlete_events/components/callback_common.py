from __future__ import annotations

import plotly.express as px


def empty_figure(title: str):
    fig = px.scatter(title=title)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(annotations=[])
    return fig

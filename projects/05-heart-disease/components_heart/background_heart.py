from pathlib import Path

from dash import html

BACKGROUND_ASSET_NAME = "illuminated-heart-held-stockcake.webp"


def _background_url():
    asset_path = Path(__file__).resolve().parent.parent / "assets" / BACKGROUND_ASSET_NAME
    if asset_path.exists():
        version = int(asset_path.stat().st_mtime)
        return f"/assets/{BACKGROUND_ASSET_NAME}?v={version}"
    return f"/assets/{BACKGROUND_ASSET_NAME}"


def render(children):
    background_image_url = _background_url()
    return html.Div(
        style={
            'backgroundImage': f'url({background_image_url})',
            'backgroundSize': 'cover',
            'backgroundPosition': 'center',
            'backgroundRepeat': 'no-repeat',
            'minHeight': '100vh',
            'color': '#ffffff',
            'fontFamily': 'Arial, sans-serif'
        },
        children=[
            html.Div(
                style={
                    'backgroundColor': 'rgba(0, 0, 0, 0.62)',
                    'minHeight': '100vh',
                    'padding': '20px'
                },
                children=children
            )
        ]
    )
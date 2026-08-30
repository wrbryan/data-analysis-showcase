from dash import html, dcc
import dash_bootstrap_components as dbc

def render(sex_options, category_options):
    return dbc.Row([
        dbc.Col([
            html.Label("Select Sex:", style={'color': '#ffffff', 'fontWeight': '600', 'textShadow': '1px 1px 3px rgba(0,0,0,0.9)'}),
            dcc.Dropdown(
                id='sex-dropdown',
                options=sex_options,
                value=[],
                multi=True,
                searchable=True
            )
        ], width=12),
        dbc.Col([
            html.Label("Select Chest Pain Type:", style={'color': '#ffffff', 'fontWeight': '600', 'textShadow': '1px 1px 3px rgba(0,0,0,0.9)'}),
            dcc.Dropdown(
                id='cp-dropdown',
                options=[],
                value=[],
                multi=True,
                searchable=True,
                placeholder='Chest pain types appear after sex selection'
            )
        ], width=12),
        dbc.Col([
            html.Label("Category To Visualize:", style={'color': '#ffffff', 'fontWeight': '600', 'textShadow': '1px 1px 3px rgba(0,0,0,0.9)'}),
            dcc.Dropdown(
                id='category-dropdown',
                options=category_options,
                value='cp',
                clearable=False,
                searchable=False
            )
        ], width=12),
        dbc.Col([
            html.Div(id='cp-list', style={'marginTop': '0.5rem', 'color': '#ffffff', 'fontWeight': '600', 'textShadow': '1px 1px 3px rgba(0,0,0,0.9)'})
        ], width=12)
    ])

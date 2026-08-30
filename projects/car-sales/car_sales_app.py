from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from util_car import get_grouped_data, get_full_data, get_manufacturers, get_models, get_models_grouped_data
from components_car import (
        background_car,
        dropdown_car,
        pie_car,
        bar_car,
        bar_h_car,
        scatter_car
    )

PATH = "Car_sales.csv"
manufacturers = get_manufacturers(PATH)

app = Dash(external_stylesheets=[dbc.themes.COSMO])

app.layout = background_car.render([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1(
                    "Car Sales Analysis",
                    className="text-center my-4",
                    style={'color': '#ffffff', 'textShadow': '2px 2px 6px rgba(0,0,0,0.85)'}
                )
            ], width=12)
        ]),
        dropdown_car.render(manufacturers),
        dbc.Row([
            dbc.Col(pie_car.render(), lg=6),
            dbc.Col(bar_car.render(), lg=6)
        ]),
        dbc.Row([
            dbc.Col(bar_h_car.render(), lg=6),
            dbc.Col(scatter_car.render(), lg=6)
        ])
    ], fluid=True)
])

@app.callback(
    Output('model-dropdown', 'options'),
    Output('model-dropdown', 'value'),
    Output('models-list', 'children'),
    Input('manufacturer-dropdown', 'value')
)
def update_models(selected_manufacturers):
    models = get_models(PATH, selected_manufacturers if selected_manufacturers else None)
    options = [{'label': m, 'value': m} for m in models]
    value = models  # auto-select all visible models for each manufacturer selection
    model_count = len(models)
    list_items = f"Available models: {model_count}" if models else 'No models available.'
    return options, value, list_items

@app.callback(
    Output('pie_chart_car', 'figure'),
    Input('manufacturer-dropdown', 'value'),
    Input('model-dropdown', 'value')
)
def update_pie(selected_manufacturers, selected_models):
    df = get_models_grouped_data(PATH, selected_manufacturers if selected_manufacturers else None, selected_models if selected_models else None)
    return pie_car.update_figure(df)

@app.callback(
    Output('bar-chart-car', 'figure'),
    Input('manufacturer-dropdown', 'value'),
    Input('model-dropdown', 'value')
)
def update_bar(selected_manufacturers, selected_models):
    df = get_models_grouped_data(PATH, selected_manufacturers if selected_manufacturers else None, selected_models if selected_models else None)
    return bar_car.update_figure(df)

@app.callback(
    Output('horizontal-bar-chart-car', 'figure'),
    Input('manufacturer-dropdown', 'value'),
    Input('model-dropdown', 'value')
)
def update_bar_h(selected_manufacturers, selected_models):
    df = get_models_grouped_data(PATH, selected_manufacturers if selected_manufacturers else None, selected_models if selected_models else None)
    return bar_h_car.update_figure(df)

@app.callback(
    Output('scatter-chart-car', 'figure'),
    Input('manufacturer-dropdown', 'value'),
    Input('model-dropdown', 'value')
)
def update_scatter(selected_manufacturers, selected_models):
    df = get_full_data(PATH, selected_manufacturers if selected_manufacturers else None, selected_models if selected_models else None)
    return scatter_car.update_figure(df)

if __name__ == '__main__':
    app.run(debug=True)
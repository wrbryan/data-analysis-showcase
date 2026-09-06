from dash import Dash, html, Input, Output
import dash_bootstrap_components as dbc
from util_heart import (
    CATEGORY_LABELS,
    get_full_data,
    get_sex_values,
    get_cp_values,
    get_category_options,
    get_category_distribution,
    get_target_by_category
)
from components_heart import (
    background_heart,
    dropdown_heart,
    pie_heart,
    bar_heart,
    bar_h_heart,
    scatter_heart
    )

SEX_LABELS = {0: "Female", 1: "Male"}
CP_LABELS = {
    0: "Typical Angina",
    1: "Atypical Angina",
    2: "Non-anginal Pain",
    3: "Asymptomatic"
}

PATH = "heart.csv"
sex_values = get_sex_values(PATH)
category_options = get_category_options()

app = Dash(external_stylesheets=[dbc.themes.COSMO])

app.layout = background_heart.render([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1(
                    "Heart Disease Analysis",
                    className="text-center my-4",
                    style={'color': '#ffffff', 'textShadow': '2px 2px 6px rgba(0,0,0,0.85)'}
                )
            ], width=12)
        ]),
        dropdown_heart.render(
            [
                {'label': SEX_LABELS.get(value, f'Sex {value}'), 'value': value}
                for value in sex_values
            ],
            category_options
        ),
        dbc.Row([
            dbc.Col(pie_heart.render(), lg=6),
            dbc.Col(bar_heart.render(), lg=6)
        ]),
        dbc.Row([
            dbc.Col(bar_h_heart.render(), lg=6),
            dbc.Col(scatter_heart.render(), lg=6)
        ])
    ], fluid=True)
])

@app.callback(
    Output('cp-dropdown', 'options'),
    Output('cp-dropdown', 'value'),
    Output('cp-list', 'children'),
    Input('sex-dropdown', 'value')
)
def update_cp_options(selected_sexes):
    cp_values = get_cp_values(PATH, selected_sexes if selected_sexes else None)
    options = [{'label': CP_LABELS.get(v, f'CP {v}'), 'value': v} for v in cp_values]
    value = cp_values
    cp_count = len(cp_values)
    list_items = f"Available chest pain types: {cp_count}" if cp_values else 'No chest pain types available.'
    return options, value, list_items

@app.callback(
    Output('pie-chart-heart', 'figure'),
    Input('sex-dropdown', 'value'),
    Input('cp-dropdown', 'value'),
    Input('category-dropdown', 'value')
)
def update_pie(selected_sexes, selected_cp, selected_category):
    df = get_category_distribution(
        PATH,
        selected_category,
        selected_sexes if selected_sexes else None,
        selected_cp if selected_cp else None
    )
    return pie_heart.update_figure(df, CATEGORY_LABELS[selected_category])

@app.callback(
    Output('bar-chart-heart', 'figure'),
    Input('sex-dropdown', 'value'),
    Input('cp-dropdown', 'value'),
    Input('category-dropdown', 'value')
)
def update_bar(selected_sexes, selected_cp, selected_category):
    df = get_category_distribution(
        PATH,
        selected_category,
        selected_sexes if selected_sexes else None,
        selected_cp if selected_cp else None
    )
    return bar_heart.update_figure(df, CATEGORY_LABELS[selected_category])

@app.callback(
    Output('horizontal-bar-chart-heart', 'figure'),
    Input('sex-dropdown', 'value'),
    Input('cp-dropdown', 'value'),
    Input('category-dropdown', 'value')
)
def update_bar_h(selected_sexes, selected_cp, selected_category):
    df = get_target_by_category(
        PATH,
        selected_category,
        selected_sexes if selected_sexes else None,
        selected_cp if selected_cp else None
    )
    return bar_h_heart.update_figure(df, CATEGORY_LABELS[selected_category])

@app.callback(
    Output('scatter-chart-heart', 'figure'),
    Input('sex-dropdown', 'value'),
    Input('cp-dropdown', 'value'),
    Input('category-dropdown', 'value')
)
def update_scatter(selected_sexes, selected_cp, selected_category):
    df = get_full_data(PATH, selected_sexes if selected_sexes else None, selected_cp if selected_cp else None)
    return scatter_heart.update_figure(df, selected_category, CATEGORY_LABELS[selected_category])

if __name__ == '__main__':
    app.run(debug=True)
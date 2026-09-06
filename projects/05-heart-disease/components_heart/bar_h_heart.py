from dash import html, dcc
import plotly.express as px

def analysis_decorator(func):
    def wrapper(df, *args, **kwargs):
        if df.empty:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.update_layout(title="No data available for selected filters")
            return fig
        return func(df, *args, **kwargs)
    return wrapper

def render():
    return html.Div([
        dcc.Graph(id='horizontal-bar-chart-heart')
    ])

@analysis_decorator
def update_figure(df, category_label):
    fig = px.bar(df, x='disease_rate', y='category_label', orientation='h', title=f'Disease Rate by {category_label}')
    fig.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0.45)',
        paper_bgcolor='rgba(0, 0, 0, 0.45)',
        title_font_color='#ffffff',
        title_font_size=16,
        xaxis_title_font_color='#ffffff',
        yaxis_title_font_color='#ffffff',
        xaxis_title='Disease Rate (%)',
        yaxis_title=category_label,
        xaxis=dict(tickfont=dict(color='#ffffff'), gridcolor='rgba(255,255,255,0.2)'),
        yaxis=dict(tickfont=dict(color='#ffffff'), gridcolor='rgba(255,255,255,0.2)'),
        font_color='#ffffff'
    )
    return fig
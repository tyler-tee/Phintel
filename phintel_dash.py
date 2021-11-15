import dash
from dash.dependencies import Input, Output
from dash import dash_table, dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as plt_io
from phintel_funcs import *

# create our custom_dark theme from the plotly_dark template
plt_io.templates["custom_dark"] = plt_io.templates["plotly_dark"]

# set the paper_bgcolor and the plot_bgcolor to a new color
plt_io.templates["custom_dark"]['layout']['paper_bgcolor'] = '#30404D'
plt_io.templates["custom_dark"]['layout']['plot_bgcolor'] = '#30404D'

# you may also want to change gridline colors if you are modifying background
plt_io.templates['custom_dark']['layout']['yaxis']['gridcolor'] = '#4f687d'
plt_io.templates['custom_dark']['layout']['xaxis']['gridcolor'] = '#4f687d'

df_primary = pd.read_csv('primary.csv')
df_aggregate = primary_db_aggregate(df_primary, 'Domain').head(10)
target_fig = px.bar(df_aggregate, x='Domain', y='URL', title='Top 10 Domains')
target_fig.layout.template = 'custom_dark'

pie_agg = primary_db_aggregate(df_primary, 'Source')
pie_fig = px.pie(pie_agg, names='Source', values='URL', title='Sources')
pie_fig.layout.template = 'custom_dark'

time_agg = primary_db_aggregate(df_primary, 'Date')
time_fig = px.line(time_agg, x='Date', y='URL', title='Links Over Time')
time_fig.layout.template = 'custom_dark'

sun_agg = primary_db_aggregate(df_primary, ['Source', 'Domain'])
sun_agg = pd.concat(sun_agg[sun_agg['Source'] == source].head() for source in ['openphish', 'phishtank', 'phishstats'])
sun_fig = px.sunburst(sun_agg, path=['Source', 'Domain'], values='URL')
sun_fig.layout.template = 'custom_dark'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

app.layout = html.Div([
    html.Div([
        dcc.Graph(figure=pie_fig)
    ], style={'display': 'inline-block', 'width': '50%'}),
    html.Div([
        dcc.Graph(figure=target_fig)
    ], style={'display': 'inline-block', 'width': '50%'}),
    html.Div([
        dcc.Graph(figure=time_fig)
    ], style={'display': 'inline-block', 'width': '50%'}),
    html.Div([
        dcc.Graph(figure=sun_fig)
    ], style={'display': 'inline-block', 'width': '50%'}),
    html.A(html.Button('Refresh Table'), id='df_refresh', n_clicks=0),
    dash_table.DataTable(
        id='table',
        columns=[{"name": col, "id": col, "selectable": True} for col in df_primary.columns],
        data=df_primary.to_dict('records'),
        editable=True,
        filter_action="native",
        sort_action="native",
        page_size=50,
        style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white'
        },
        style_data={
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white'
        },
        style_cell={'textAlign': 'left',
            'maxWidth': '180px',
            'textOverflow': 'ellipsis'
        },
    ),
    html.Div(id='table-container')
])


@app.callback(
    Output('table', 'data'),
    [Input('df_refresh', 'n_clicks')]
)
def update_table(n_clicks):
    if n_clicks is not None:
        df_updated = primary_db_update()
        return df_updated.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True)

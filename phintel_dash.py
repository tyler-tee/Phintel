import dash
from dash.dependencies import Input, Output, State
from dash import dash_table, dcc, html
from datetime import datetime
import dash_bootstrap_components as dbc
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

# Read in our source
conn = sqlite3.connect('./primary.sqlite')
df_primary = pd.read_sql('SELECT * FROM main', con=conn)
sources = list(df_primary['Source'].unique())
sources = [source for source in sources if source]
source_options = [{'label': 'All', 'value': '|'.join(sources)}]
source_options += [{'label': source.title(), 'value': source.lower()} for source in sources]

# Establish our visualizations
df_aggregate = primary_db_aggregate(df_primary, 'Domain').head(10)
bar_fig = px.bar(df_aggregate, x='Domain', y='URL', title='Top 10 Domains')
bar_fig.layout.template = 'custom_dark'

pie_agg = primary_db_aggregate(df_primary, 'Source')
pie_fig = px.pie(pie_agg, names='Source', values='URL', title='Breakdown by Source')
pie_fig.layout.template = 'custom_dark'

time_agg = df_primary.copy()
time_agg['Date'] = time_agg['Date'].fillna('2021-01-01').apply(lambda x: pd.to_datetime(x, errors='coerce').strftime('%Y-%m'))
time_agg = primary_db_aggregate(time_agg, 'Date').sort_values(by='Date', ascending=True)
time_fig = px.line(time_agg, x='Date', y='URL', title='Links Over Time', range_x=['2021-01', datetime.datetime.now().strftime('%Y-%m')])
time_fig.layout.template = 'custom_dark'

sun_agg = primary_db_aggregate(df_primary, ['Source', 'Domain'])
sun_agg = pd.concat(sun_agg[sun_agg['Source'] == source].head() for source in sources)
sun_fig = px.sunburst(sun_agg, path=['Source', 'Domain'], values='URL', title='Top Domains by Source')
sun_fig.layout.template = 'custom_dark'

# Sidebar construction
navbar = dbc.NavbarSimple(
    children=[
        dbc.Button("Data Exploration", outline=True, className="mr-1", id="btn_sidebar"),
        dbc.NavItem(dbc.NavLink("Visualizations", href="#")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("More pages", header=True),
                dbc.DropdownMenuItem("Raw Data", href="#")
            ],
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="Phintel",
    brand_href="#",
    color="dark",
    dark=True,
    fluid=True,
)

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 62.5,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "4rem 1rem 2rem"
}

SIDEBAR_HIDEN = {
    "position": "fixed",
    "top": 62.5,
    "left": "-16rem",
    "bottom": 0,
    "width": "16rem",
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0rem 0rem"
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "transition": "margin-left .5s",
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem"
}

CONTENT_STYLE1 = {
    "transition": "margin-left .5s",
    "margin-left": "2rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem"
}

sidebar = html.Div(
    [
        html.H6("Tools", className="display-4"),
        html.Hr(),
        html.P("Explore Phintel's underlying dataset.", className="lead"),
        dbc.Nav(
            [
                dbc.NavLink("Visualizations", href="/page-1", id="page-1-link"),
                dbc.NavLink("Raw Data", href="/page-2", id="page-2-link"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    id="sidebar",
    style=SIDEBAR_STYLE,
)

content = html.Div(
    id="page-content",
    style=CONTENT_STYLE)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], title='Phintel', suppress_callback_exceptions=True)

"""
app.layout = html.Div([
    html.Div([
            dcc.Store(id='side_click'),
            dcc.Location(id="url"),
            navbar,
            sidebar,
            content
            ]),
    html.H1(children='Phintel', style={'textAlign': 'center'}),
    dcc.Tabs([
        dcc.Tab(label='Visualizations', style={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
        children=[
               html.Div([
                    dcc.Graph(figure=pie_fig, id='pie_fig')
                ], style={'display': 'inline-block', 'width': '50%', 'border': '2px black solid'}),
                html.Div([
                    dcc.Dropdown(
                                options=source_options,
                                value='openphish|phishstats|phishtank|urlhaus',
                                clearable=False,
                                id='source_dropdown',
                                # style={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'black'}
                                className='custom-dropdown'
                                ),
                    dcc.Graph(figure=bar_fig, id='bar_fig')
                ], style={'display': 'inline-block', 'width': '50%', 'border': '2px black solid'}),
                html.Div([
                    dcc.Graph(figure=time_fig, id='time_fig')
                ], style={'display': 'inline-block', 'width': '50%', 'border': '2px black solid'}),
                html.Div([
                    dcc.Graph(figure=sun_fig, id='sun_fig')
                ], style={'display': 'inline-block', 'width': '50%', 'border': '2px black solid'}) 
        ]),
        dcc.Tab(label='Raw Data', style={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
        children=[
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
        ])
])
"""

app.layout = html.Div([
    html.Div([
            dcc.Store(id='side_click'),
            dcc.Location(id="url"),
            navbar,
            sidebar,
            content
            ]),
])

"""
@app.callback(
    Output(component_id='table', component_property='data'),
    [Input(component_id='df_refresh', component_property='n_clicks')]
)
def update_table(n_clicks):
    if n_clicks is not None:
        df_updated = primary_db_update()
        return df_updated.to_dict('records')
"""

@app.callback(
    Output(component_id='bar_fig', component_property='figure'),
    [Input(component_id='source_dropdown', component_property='value')]
)
def update_bar(value):
    df_bar = df_primary[df_primary['Source'].fillna('').str.contains(value)]
    df_bar = primary_db_aggregate(df_bar, 'Domain').head(10)
    bar_fig = px.bar(df_bar, x='Domain', y='URL', title='Top 10 Domains')
    bar_fig.layout.template = 'custom_dark'

    return bar_fig


@app.callback(
    [
        Output("sidebar", "style"),
        Output("page-content", "style"),
        Output("side_click", "data"),
    ],
    [Input("btn_sidebar", "n_clicks")],
    [State("side_click", "data"),]
)
def toggle_sidebar(n, nclick):
    if n:
        if nclick == "SHOW":
            sidebar_style = SIDEBAR_HIDEN
            content_style = CONTENT_STYLE1
            cur_nclick = "HIDDEN"
        else:
            sidebar_style = SIDEBAR_STYLE
            content_style = CONTENT_STYLE
            cur_nclick = "SHOW"
    else:
        sidebar_style = SIDEBAR_STYLE
        content_style = CONTENT_STYLE
        cur_nclick = 'SHOW'

    return sidebar_style, content_style, cur_nclick

# this callback uses the current pathname to set the active state of the
# corresponding nav link to true, allowing users to tell see page they are on
@app.callback(
    [Output(f"page-{i}-link", "active") for i in range(1, 3)],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        # Treat page 1 as the homepage / index
        return True, False
    return [pathname == f"/page-{i}" for i in range(1, 3)]


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ["/", "/page-1"]:
        page_one_content = html.Div([
               html.Div([
                    dcc.Graph(figure=pie_fig, id='pie_fig')
                ], style={'display': 'inline-block', 'width': '50%', 'border': '2px black solid'}),
                html.Div([
                    dcc.Dropdown(
                                options=source_options,
                                value='openphish|phishstats|phishtank|urlhaus',
                                clearable=False,
                                id='source_dropdown',
                                # style={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'black'}
                                className='custom-dropdown'
                                ),
                    dcc.Graph(figure=bar_fig, id='bar_fig')
                ], style={'display': 'inline-block', 'width': '50%', 'border': '2px black solid'}),
                html.Div([
                    dcc.Graph(figure=time_fig, id='time_fig')
                ], style={'display': 'inline-block', 'width': '50%', 'border': '2px black solid'}),
                html.Div([
                    dcc.Graph(figure=sun_fig, id='sun_fig')
                ], style={'display': 'inline-block', 'width': '50%', 'border': '2px black solid'}) 
                            ])
        return page_one_content
    elif pathname == "/page-2":
        page_two_content = html.Div([
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
        return page_two_content
    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )

if __name__ == '__main__':
    app.run_server(debug=True)

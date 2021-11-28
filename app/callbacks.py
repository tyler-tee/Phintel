import dash
from dash.dependencies import Input, Output, State
from dash import dash_table, dcc
from layouts import *
from predict.phintel_predict import *


app = dash.Dash('Phintel', external_stylesheets=[dbc.themes.SOLAR],
                title='Phintel', suppress_callback_exceptions=True)
server = app.server

@app.callback(
    Output(component_id='bar_fig', component_property='figure'),
    [Input(component_id='source_select', component_property='value')]
)
def update_bar(value):
    df_bar = df_primary[df_primary['Source'].fillna('').str.contains(value)]
    df_bar = primary_db_aggregate(df_bar, 'Domain').head(10)
    bar_fig = px.bar(df_bar, x='Domain', y='URL', title='Top 10 Domains')
    bar_fig.layout.template = 'custom_dark'
    bar_fig.update_traces(marker_color='#2aa198')

    return bar_fig


@app.callback(
    [
        Output("sidebar", "style"),
        Output("page-content", "style"),
        Output("side_click", "data"),
    ],
    [Input("btn_sidebar", "n_clicks"),
     Input("url", "pathname")],
    [State("side_click", "data"),]
)
def toggle_sidebar(n, pathname, nclick):
    if pathname in ["/", "/page-1"]:
        sidebar_style = SIDEBAR_HIDDEN
        content_style = CONTENT_STYLE1
        cur_nclick = "HIDDEN"
    else:
        if n:
            if nclick == "SHOW":
                sidebar_style = SIDEBAR_HIDDEN
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
    [Output(f"page-{i}-link", "active") for i in range(1, 6)],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        # Treat page 1 as the homepage / index
        return True, False, False, False, False
    return [pathname == f"/page-{i}" for i in range(1, 6)]


@app.callback(Output("navbar", "style"),
              Input("url", "pathname"))
def navbar_toggle(pathname):
    if pathname in ["/", "/page-1"]:
        nav_style = {'display': 'none'}
    else:
        nav_style = {'display': 'block'}
    
    return nav_style


@app.callback(Output("page-content", "children"),
              [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ["/", "/page-1"]:
        page_one_content = dbc.Container(
            [
                dbc.Row(
                    [dbc.Col()], class_name='h-50'
                ),
                dbc.Row(
                    [
                        dbc.Col([
                            html.H1('Phintel'),
                            html.H5('Facilitating the extraction, aggregation, and exploration of phishing intelligence.'),
                            dbc.Button('Visualizations', href='/page-2', color='info', style={'margin': '3px'}), dbc.Button('Raw Data', href='/page-3', color='info', style={'margin': '3px', 'padding-left': '26px', 'padding-right': '26px'}),
                            dbc.Button('ML Analysis', href='/page-4', color='info', style={'margin': '3px', 'padding-left': '19px', 'padding-right': '19px'}), dbc.Button('About', href='/page-5', color='info', style={'margin': '3px', 'padding-left': '37px', 'padding-right': '37px'})
                        ],
                        style={'height': '100%', 'text-align': 'center'})
                    ], class_name='h-50'
                )
            ], style={'height': '100vh'}
        )

        return page_one_content
    
    elif pathname == "/page-2":
        page_two_content = html.Div([
            dbc.Row([
                dbc.Col(id='card1', children=[card1], md=3),
                dbc.Col(id='card2', children=[card2], md=3),
                dbc.Col(id='card3', children=[card3], md=3),
                dbc.Col(id='card4', children=[card4], md=3)
                    ]),
            html.Hr(),
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                dbc.Select(
                                    options=source_options,
                                    value='openphish|phishstats|phishtank|urlhaus',
                                    id='source_select',
                                    style={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
                                    placeholder='All Sources'
                                        ),
                                dcc.Graph(figure=bar_fig, id='bar_fig')
                                    ])
                                ], style={'width': '50%', 'height': 'auto', 'border': '2px black solid'}),
                        dbc.Col([
                            html.Div([
                                dcc.Graph(figure=sun_fig, id='sun_fig')
                                    ])
                                ], style={'width': '50%', 'height': 'auto', 'border': '2px black solid'})
                            ], className="g-0", align='end'),
                        ]),     
                html.Div([
                    dcc.Graph(figure=time_fig, id='time_fig')
                        ], style={'display': 'inline-block', 'width': '100%', 'border': '2px black solid'}),
               html.Div([
                    dcc.Graph(figure=pie_fig, id='pie_fig')
                        ], style={'display': 'inline-block', 'width': '50%', 'border': '2px black solid'}),
               html.Div([
                    dcc.Graph(figure=target_fig, id='target_fig')
                        ], style={'display': 'inline-block', 'width': '50%', 'border': '2px black solid'})
                            ])
        
        return page_two_content
    
    elif pathname == "/page-3":
        page_three_content = html.Div([
                                    html.H1("Full Dataset", style={"text-align": "center"}),
                                    html.Hr(),
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
        
        return page_three_content
    
    elif pathname == "/page-4":
        page_four_content = html.Div([
                                    html.H1("Predictive Analysis", style={"text-align": "center"}),
                                    html.Hr(),
                                    html.Div([
                                    dbc.Label("URL Analyzer"),
                                    dbc.Input(id='ml_input', placeholder='https://Malicious-URL.bad', value='https://Malicious-URL.bad',
                                              debounce=True, inputmode='url'),
                                    dbc.FormText("Supply a URL for analysis and Phintel will use rudimentary machine learning to assign it a value of good or bad.*\n",
                                                 style={'font-style': 'italic'}),
                                    html.Br(),
                                    html.Div(id='ml_analysis')
                                            ]),
                                    html.Footer(
                                        dbc.FormText("""*This feature is highly experimental and some errors should be expected.\n
                                                    Sample models are provided for testing, but it's advisable to train your own if you'll be considering a production use case.""",
                                                    style={'font-style': 'italic', 'bottom': 0, 'position': 'fixed', 'background-color': 'rgb(0, 0, 0, 0.0)'})
                                                )
                                    ])
        
        return page_four_content
    
    elif pathname == "/page-5":
        page_five_content = html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.H1('Phintel'),
                                    html.H5('Facilitating the extraction, aggregation, and exploration of phishing intelligence.')
                                        ], align='center', style={'textAlign': 'center', 'verticalAlign': 'center',
                                                'align-items': 'center', 'justify-content': 'center'})
                                    ], align='center', justify='center',
                                        style={'textAlign': 'center', 'verticalAlign': 'center',
                                                'align-items': 'center', 'justify-content': 'center'}),
                            html.Br(),
                            html.Hr(),
                            html.Br(),
                            html.H2('Current Sources', style={'textAlign': 'center'}),
                            html.Br(),
                            dbc.Row([
                                dbc.Col(dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H3("Openphish", className="card-title"),
                                            html.Br(),
                                            html.Br(),
                                            html.H6("OpenPhish is a fully automated self-contained platform for phishing intelligence. OpenPhish reports only new and live phishing URLs.",
                                                    className="card-subtitle", style={'font-style': 'italic'}),
                                            html.Br(),
                                            html.Br(),
                                            dbc.Button("Visit Site", href='https://openphish.com/', color='info')
                                            ]
                                    ),
                                    # color="info",
                                    inverse=True,
                                    outline=True
                                        )),
                                dbc.Col(dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H3("Phishstats", className="card-title"),
                                            html.Br(),
                                            html.Br(),
                                            html.H6("Fighting phishing and cybercrime since 2014 by gathering, enhancing and sharing phishing information with the infosec community.",
                                                    className="card-subtitle", style={'font-style': 'italic'}),
                                            html.Br(),
                                            html.Br(),
                                            dbc.Button("Visit Site", href="https://phishstats.info/", color='info')
                                            ]
                                    ),
                                    # color="info",
                                    inverse=True,
                                    outline=True
                                        ))   
                                    ]),
                            dbc.Row([
                                dbc.Col(dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H3("Phishtank", className="card-title"),
                                            html.Br(),
                                            html.Br(),
                                            html.H6("PhishTank is a collaborative clearing house for data and information about phishing on the Internet. Operated by Cisco Talos Intelligence Group.",
                                                    className="card-subtitle", style={'font-style': 'italic'}),
                                            html.Br(),
                                            html.Br(),
                                            dbc.Button("Visit Site", href='https://phishtank.org/', color='info')
                                            ]
                                    ),
                                    # color="info",
                                    inverse=True,
                                    outline=True
                                        )),
                                dbc.Col(dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H3("URLhaus", className="card-title"),
                                            html.Br(),
                                            html.Br(),
                                            html.H6("URLhaus is a project from abuse.ch with the goal of sharing malicious URLs that are being used for malware distribution.",
                                                    className="card-subtitle", style={'font-style': 'italic'}),
                                            html.Br(),
                                            html.Br(),
                                            dbc.Button("Visit Site", href='https://urlhaus.abuse.ch/', color='info')
                                            ]
                                    ),
                                    # color="info",
                                    inverse=True,
                                    outline=True
                                        ))   
                                    ]),
                            html.Hr()
                                                ])
        
        return page_five_content
    
    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


@app.callback(Output("ml_analysis", "children"),
            [Input("ml_input", "value")])
def analyze_url(value):
    if (value != 'https://Malicious-URL.bad') and ('.' in value):
        try:
            model, vectorizer = load_trained('./predict/ml_model.pkl', './predict/ml_vectorizer.pkl')
            model_loaded = True
            result = url_predict([value], vectorizer=vectorizer, model=model)
            result = 'Malicious' if result[0] == 'bad' else 'Benign' if result[0] == 'good' else 'Unknown'
            return f"Phintel's analysis for {value}: {result}"
        except Exception as e:
            return f"Phintel experienced an error analyzing the supplied URL:\n{e}"
    else:
        return ""

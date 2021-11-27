import dash
from dash.dependencies import Input, Output, State
from dash import dash_table, dcc, html
import datetime
from io import StringIO
import pandas as pd
import requests
from config import phishtank_api_key
from layouts import *
import plotly.express as px
from predict.phintel_predict import *
import sqlite3
from urllib.parse import urlparse

otx_headers = {'X-OTX-API-KEY': ''}
otx_baseapi = 'https://otx.alienvault.com/api/v1'
phishtank_baseapi = "https://checkurl.phishtank.com/checkurl/"
phishtank_db_url = f"http://data.phishtank.com/data/{phishtank_api_key}/online-valid.csv"


# Read in our source
conn = sqlite3.connect('./data/primary.sqlite')
df_primary = pd.read_sql('SELECT * FROM main', con=conn)
sources = list(df_primary['Source'].unique())
sources = [source for source in sources if source]
source_options = [{'label': 'All Sources', 'value': '|'.join(sources)}]
source_options += [{'label': source.title(), 'value': source.lower()} for source in sources]

def create_card(title, content):
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H4(title, className="card-title"),
                html.Br(),
                html.Br(),
                html.H2(content, className="card-subtitle"),
                html.Br(),
                html.Br(),
                ]
        ),
        # color="info",
        inverse=True,
        outline=True
    )
    return(card)


def domain_parser(url):
    t = urlparse(str(url))
    parsed = '.'.join(t.netloc.split('.')[-2:])

    if parsed == 'com':
        return t
    else:
        return parsed


def openphish_update() -> pd.DataFrame:  # Updated every 12 hours
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
    response = requests.get("https://openphish.com/feed.txt")

    if response.status_code == 200:
        openphish_feed = response.text.split('\n')

        df_openphish = pd.DataFrame(columns=['URL', 'Source'])

        df_openphish['URL'] = openphish_feed
        df_openphish = df_openphish.drop_duplicates(subset='URL', keep='first')
        df_openphish['URL'] = df_openphish['URL'].str.lower()

        df_openphish['Source'] = 'openphish'
        df_openphish['Date'] = timestamp
        df_openphish['Notes'] = 'Free Dataset'
        df_openphish['Target'] = 'Other'

        return df_openphish


def phishstats_update() -> pd.DataFrame:  # Updated every 1.5 hours
    # We're doing this with requests to handle our headers - PhishStats is sensitive
    response = requests.get("https://phishstats.info/phish_score.csv")
    phishstats_cols = ['Date', 'Notes', 'URL', 'IP']

    if response.status_code == 200:
        try:
            data = StringIO(response.content.decode("utf-8"))
            df_phishstats = pd.read_csv(data, skiprows=9)
        except Exception as e:
            print(e)
            df_phishstats = pd.DataFrame(columns=phishstats_cols, data=None)

        df_phishstats.columns = phishstats_cols
        df_phishstats.drop(columns=['IP'], inplace=True)

        df_phishstats['URL'] = df_phishstats['URL'].str.lower()
        df_phishstats = df_phishstats.drop_duplicates(subset='URL', keep='first')  # Remove duplicate URL's
        df_phishstats = df_phishstats[~df_phishstats['Date'].str.contains(',')]  # Remove anomalies

        # Establish standardized columns
        df_phishstats['Notes'] = 'Score: ' + df_phishstats['Notes'].astype(str)
        df_phishstats['Source'] = 'phishstats'
        df_phishstats['Target'] = 'Other'

        return df_phishstats


def phishtank_update() -> pd.DataFrame:  # Updated every 1 hour
    phishtank_cols = ['url', 'phish_detail_url', 'submission_time', 'target']  # Expected columns

    try:
        df_phishtank = pd.read_csv(phishtank_db_url, usecols=phishtank_cols)  # Read csv into dataframe from url
    except Exception as e:
        print(e)
        df_phishtank = pd.DataFrame(columns=phishtank_cols, data=None)

    # Standardize our column names
    df_phishtank.rename(columns={"url": "URL", "phish_detail_url": "Notes",
                                 "submission_time": "Date", "target": "Target"},
                        inplace=True)

    df_phishtank['URL'] = df_phishtank['URL'].str.lower()
    df_phishtank = df_phishtank.drop_duplicates(keep='first', subset='URL')  # Get rid of duplicate URL's
    df_phishtank['Source'] = 'phishtank'  # Tag data with source

    return df_phishtank


def urlhaus_update() -> pd.DataFrame:  # Updated every 5 minutes
    try:
        df_haus = pd.read_csv('https://urlhaus.abuse.ch/downloads/csv/',
                              compression='zip', skiprows=8)

        df_haus.rename(columns={"url": "URL", "dateadded": "Date",
                                "threat": "Notes"}, inplace=True)
        df_haus['URL'] = df_haus['URL'].str.lower()
        df_haus = df_haus.drop_duplicates(keep='first', subset='URL')
        df_haus = df_haus[['URL', 'Date', 'Notes']]
        df_haus['Source'] = 'urlhaus'
        df_haus['Target'] = 'Other'

        return df_haus
        
    except Exception as e:
        print(e)


def primary_db_update() -> pd.DataFrame:
    # Gather our initial dataframes from all available sources
    df_openphish = openphish_update()
    df_phishstats = phishstats_update()
    df_phishtank = phishtank_update()
    df_haus = urlhaus_update()

    # Create primary dataframe from our component dataframes
    df_primary = pd.concat([df_openphish, df_phishstats, df_phishtank, df_haus])

    # Try and append dataframe based on established data - Move on if the file isn't available
    try:
        prev_primary = pd.read_csv('./data/primary.csv', on_bad_lines='skip')
        df_primary = df_primary.append(prev_primary)
    except FileNotFoundError:
        pass
    
    try:
        conn = sqlite3.connect('./data/primary.sqlite')
        primary_db = pd.read_sql('SELECT * FROM main', con=conn)
        df_primary = df_primary.append(primary_db)
    except Exception as e:
        print(e)

    
    df_primary['URL'] = df_primary['URL'].str.lower()  # Just to ensure consistency among our URL's
    df_primary = df_primary.drop_duplicates(subset='URL', keep='first')  # Filter out any duplicate URL's
    df_primary['Domain'] = df_primary['URL'].apply(lambda x: domain_parser(x)) # Parse domains from our URL's
    df_primary['Date'] = pd.to_datetime(df_primary['Date'])  # Make sure our date is in ISO 8601
    df_primary['Source'] = df_primary['Source'].str.lower()

    if not df_primary.empty:
        df_primary.to_csv('./data/primary.csv', index=False)  # Write primary dataframe to disk as a csv
        df_primary.to_sql('main', conn, if_exists='replace', index=False)

    return df_primary


def primary_db_search(search_term: str, dataframe: pd.DataFrame,
                      search_type: str = 'exact', column: str = 'URL'):
    if search_type != 'exact':
        results = dataframe[dataframe[column].str.contains(search_term, na=False)]
    else:
        results = dataframe.loc[dataframe[column] == search_term]

    return not results.empty


def primary_db_aggregate(dataframe: pd.DataFrame, agg_value: str) -> pd.DataFrame:
    df_aggregate = dataframe.groupby(agg_value).agg({'URL': 'nunique'}).reset_index()  # Aggregate targets by attempts

    df_aggregate = df_aggregate.sort_values('URL', ascending=False)

    return df_aggregate


def otx_url_search(url: str, section: str = 'general') -> dict:
    response = requests.get(f'{otx_baseapi}/indicators/url/{url}/{section}',
                            headers=otx_headers)

    if response.status_code == 200 and 'endpoint not found' not in response.text:
        return response.json()


def otx_domain_search(domain: str, section: str = 'general') -> dict:
    response = requests.get(f'{otx_baseapi}/indicators/domain/{domain}/{section}',
                            headers=otx_headers)

    if response.status_code == 200 and 'endpoint not found' not in response.text:
        return response.json()


def rawhttp_sub(url: str) -> str:
    user_agent = ("Mozilla/5.0 (Windows NT 10.0; WOW64)"
                  "AppleWebKit/537.36 (KHTML, like Gecko)"
                  "Chrome/53.0.2785.143 Safari/537.36")

    payload = {'ua': user_agent,
               'url': url}

    endpoint = 'https://rawhttp.com/getimage'

    response = requests.post(endpoint, json=payload)

    if response.status_code == 200 and 'errorMessage' not in response.text:
        return response.text


card1 = create_card("Openphish", f"{len(df_primary[df_primary['Source'] == 'openphish']):,}")
card2 = create_card("Phishstats", f"{len(df_primary[df_primary['Source'] == 'phishstats']):,}")
card3 = create_card("Phishtank", f"{len(df_primary[df_primary['Source'] == 'phishtank']):,}")
card4 = create_card("URLhaus", f"{len(df_primary[df_primary['Source'] == 'urlhaus']):,}")

# Establish our visualizations
bar_agg = primary_db_aggregate(df_primary, 'Domain').head(10)
bar_fig = px.bar(bar_agg, x='Domain', y='URL', title='Top 10 Domains')
bar_fig.layout.template = 'custom_dark'
bar_fig.update_traces(marker_color='#2aa198')

pie_agg = primary_db_aggregate(df_primary, 'Source')
pie_fig = px.pie(pie_agg, names='Source', values='URL', title='Breakdown by Source', hole=.55)
pie_fig.layout.template = 'custom_dark'

time_agg = df_primary.copy()
time_agg['Date'] = time_agg['Date'].fillna('2021-01-01').apply(lambda x: pd.to_datetime(x, errors='coerce').strftime('%Y-%m'))
time_agg = primary_db_aggregate(time_agg, 'Date').sort_values(by='Date', ascending=True)
time_fig = px.line(time_agg, x='Date', y='URL', title='Links Over Time', range_x=['2021-01', datetime.datetime.now().strftime('%Y-%m')])
time_fig.layout.template = 'custom_dark'
time_fig.update_traces(line_color='#2aa198')

sun_agg = primary_db_aggregate(df_primary, ['Source', 'Domain'])
sun_agg = pd.concat(sun_agg[sun_agg['Source'] == source].head() for source in sources)
sun_fig = px.sunburst(sun_agg, path=['Source', 'Domain'], values='URL', title='Top Domains by Source')
sun_fig.layout.template = 'custom_dark'

target_agg = df_primary[df_primary['Target'] != 'Other']
target_agg = primary_db_aggregate(target_agg, 'Target').head(10)
target_fig = px.bar(target_agg, x='Target', y='URL', title='Top Identified Targets')
target_fig.layout.template = 'custom_dark'
target_fig.update_traces(marker_color='#2aa198')

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
                                ], style={'width': 'auto', 'height': 'auto', 'border': '2px black solid'}),
                        dbc.Col([
                            html.Div([
                                dcc.Graph(figure=sun_fig, id='sun_fig')
                                    ])
                                ], style={'width': 'auto', 'height': 'auto', 'border': '2px black solid'})
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
                                    dbc.Input(id='ml_input', placeholder='https://Malicious-URL.bad', value='https://Malicious-URL.bad', style={'color': 'white'}, debounce=True, inputmode='url'),
                                    dbc.FormText("Supply a URL for analysis and Phintel will use rudimentary machine learning to assign it a value of good or bad.*\n",
                                                 style={'font-style': 'italic'}),
                                    html.Br(),
                                    html.Div(id='ml_analysis')
                                    ]),
                                    html.Footer(
                                        dbc.FormText("""*This feature is highly experimental and some errors should be expected.\n
                                                    Sample models are provided for testing, but it's advisable to train your own if you'll be considering a production use case.""",
                                                    style={'font-style': 'italic', 'bottom': 0, 'position': 'fixed'})
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

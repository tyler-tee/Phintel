from config import phishtank_api_key
import datetime
from dash import html
import dash_bootstrap_components as dbc
from io import StringIO
import pandas as pd
import plotly.io as plt_io
import plotly.express as px
import requests
import sqlite3
from urllib.parse import urlparse


otx_headers = {'X-OTX-API-KEY': ''}
otx_baseapi = 'https://otx.alienvault.com/api/v1'
phishtank_baseapi = "https://checkurl.phishtank.com/checkurl/"
phishtank_db_url = f"http://data.phishtank.com/data/{phishtank_api_key}/online-valid.csv"


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


def otx_domain_search(domain: str, section: str = 'general') -> dict:
    response = requests.get(f'{otx_baseapi}/indicators/domain/{domain}/{section}',
                            headers=otx_headers)

    if response.status_code == 200 and 'endpoint not found' not in response.text:
        return response.json()


def otx_url_search(url: str, section: str = 'general') -> dict:
    response = requests.get(f'{otx_baseapi}/indicators/url/{url}/{section}',
                            headers=otx_headers)

    if response.status_code == 200 and 'endpoint not found' not in response.text:
        return response.json()


def primary_db_aggregate(dataframe: pd.DataFrame, agg_value: str) -> pd.DataFrame:
    df_aggregate = dataframe.groupby(agg_value).agg({'URL': 'nunique'}).reset_index()  # Aggregate targets by attempts

    df_aggregate = df_aggregate.sort_values('URL', ascending=False)

    return df_aggregate


def primary_db_search(search_term: str, dataframe: pd.DataFrame,
                      search_type: str = 'exact', column: str = 'URL'):
    if search_type != 'exact':
        results = dataframe[dataframe[column].str.contains(search_term, na=False)]
    else:
        results = dataframe.loc[dataframe[column] == search_term]

    return not results.empty


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


# create our custom_dark theme from the plotly_dark template
plt_io.templates["custom_dark"] = plt_io.templates["plotly_dark"]

# set the paper_bgcolor and the plot_bgcolor to a new color
plt_io.templates["custom_dark"]['layout']['paper_bgcolor'] = 'rgb(7, 54, 66, 0.8)'
plt_io.templates["custom_dark"]['layout']['plot_bgcolor'] = '#002b36'

# you may also want to change gridline colors if you are modifying background
plt_io.templates['custom_dark']['layout']['yaxis']['gridcolor'] = '#586e75'
plt_io.templates['custom_dark']['layout']['xaxis']['gridcolor'] = '#586e75'

# Navbar construction
navbar = dbc.NavbarSimple(
    children=[
        dbc.Button("Tools", outline=True, className="mr-1", id="btn_sidebar"),
        dbc.NavItem(dbc.NavLink("Home", href="/page-1")),
        dbc.DropdownMenu(
            children=[
                #dbc.DropdownMenuItem("More", header=True),
                dbc.DropdownMenuItem("Home", href="/page-1"),
                dbc.DropdownMenuItem("Visualizations", href="/page-2"),
                dbc.DropdownMenuItem("Raw Data", href="/page-3"),
                dbc.DropdownMenuItem("Predictive Analysis", href="/page-4"),
                dbc.DropdownMenuItem("OSINT", href="/page-5"),
                dbc.DropdownMenuItem("About", href="/page-6")
            ],
            nav=True,
            in_navbar=True,
            label="More Pages",
        ),
    ],
    brand="Phintel",
    brand_href="#",
    color="dark",
    dark=True,
    fluid=True,
    id='navbar'
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

SIDEBAR_HIDDEN = {
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
                dbc.NavLink("Home", href="/page-1", id="page-1-link"),
                dbc.NavLink("Visualizations", href="/page-2", id="page-2-link"),
                dbc.NavLink("Raw Data", href="/page-3", id="page-3-link"),
                dbc.NavLink("Predictive Analysis", href="/page-4", id="page-4-link"),
                dbc.NavLink("OSINT", href="/page-5", id="page-5-link"),
                dbc.NavLink("About", href="/page-6", id="page-6-link")
            ],
            vertical=True,
            pills=True,
        ),
    ],
    id="sidebar",
    style=SIDEBAR_HIDDEN,
)

content = html.Div(
    id="page-content",
    style=CONTENT_STYLE1)


# Read in our source
conn = sqlite3.connect('./data/primary.sqlite')
df_primary = pd.read_sql('SELECT * FROM main', con=conn)
sources = list(df_primary['Source'].unique())
sources = [source for source in sources if source]
source_options = [{'label': 'All Sources', 'value': '|'.join(sources)}]
source_options += [{'label': source.title(), 'value': source.lower()} for source in sources]


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


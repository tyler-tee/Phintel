from dash import html
import dash_bootstrap_components as dbc
import plotly.io as plt_io
import plotly.express as px
from helpers import *


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


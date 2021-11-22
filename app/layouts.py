from dash import html
import dash_bootstrap_components as dbc

import plotly.io as plt_io

# create our custom_dark theme from the plotly_dark template
plt_io.templates["custom_dark"] = plt_io.templates["plotly_dark"]

# set the paper_bgcolor and the plot_bgcolor to a new color
plt_io.templates["custom_dark"]['layout']['paper_bgcolor'] = '#30404D'
plt_io.templates["custom_dark"]['layout']['plot_bgcolor'] = '#30404D'

# you may also want to change gridline colors if you are modifying background
plt_io.templates['custom_dark']['layout']['yaxis']['gridcolor'] = '#4f687d'
plt_io.templates['custom_dark']['layout']['xaxis']['gridcolor'] = '#4f687d'

# Navbar construction
navbar = dbc.NavbarSimple(
    children=[
        dbc.Button("Data Exploration", outline=True, className="mr-1", id="btn_sidebar"),
        dbc.NavItem(dbc.NavLink("Home", href="/page-1")),
        dbc.DropdownMenu(
            children=[
                #dbc.DropdownMenuItem("More", header=True),
                dbc.DropdownMenuItem("Home", href="/page-1"),
                dbc.DropdownMenuItem("Visualizations", href="/page-2"),
                dbc.DropdownMenuItem("Raw Data", href="/page-3"),
                dbc.DropdownMenuItem("Predictive Analysis", href="/page-4")
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
                dbc.NavLink("Predictive Analysis", href="/page-4", id="page-4-link")
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



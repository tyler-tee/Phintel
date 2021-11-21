from dash import html
from callbacks import *

app.layout = html.Div([
            dcc.Store(id='side_click'),
            dcc.Location(id="url"),
            navbar,
            sidebar,
            content
],)

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port='8050', debug=True)

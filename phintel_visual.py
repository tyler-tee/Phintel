import dash
from dash.dependencies import Input, Output
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

df_primary = pd.read_csv('primary.csv')

app = dash.Dash(__name__)

app.layout = html.Div([
    dash_table.DataTable(
        id='table',
        columns=[{"name": col, "id": col, "selectable": True} for col in df_primary.columns],
        data=df_primary.to_dict('records'),
        editable=True,
        filter_action="native",
        sort_action="native",
        page_size=1000,
        style_cell={'textAlign': 'left',
                    'maxWidth': '180px',
                    'textOverflow': 'ellipsis'},

        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        }
    ),
    html.Div(id='table-container')
])

if __name__ == '__main__':
    app.run_server(debug=True)

import dash
from dash import dcc, html, Input, Output
import requests
import pandas as pd
import plotly.express as px

app = dash.Dash(__name__)

df = pd.read_excel(r'cmdb_ci_all.xlsx')


# %%
app.layout = html.Div(children=[
    html.H1("Dashboard com Dados da CMDB"),
    html.Div(children=[
        html.H2("Gráfico de Barras"),
        dcc.Graph(
            id='bar-chart',
            figure=px.bar(df, x='used_for', y='sys_class_name')
        )
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)



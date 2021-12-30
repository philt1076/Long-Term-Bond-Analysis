import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from dash import dash_table as dtable
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np
import datetime

# Read in yield predictions and historical yield data
full_table = pd.read_csv('data\\full_results.csv', parse_dates = ['Date'])
pred_indicators = full_table['Pred Type'].unique()
countries = full_table['Country'].unique()

# Read in credit rating data
credit = pd.read_csv('data\\sp_dash.csv')

# Read in ESG data
esg = pd.read_csv('data\\esg_dash.csv')

# Set year options to all years in esg data set
explore_years = np.arange(2010, 2019)

# Include style sheet to align graphs correctly
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Create markdown text for links at bottom
my_text = '''
###### Report

See [report]() for more information on how these predictions were generated.

###### Data Sources

The data shown above can be found from the following sources:

- [Yield Data](https://fred.stlouisfed.org/)
- [Credit Ratings](https://disclosure.spglobal.com/ratings/en/regulatory/ratingshistory)
- [ESG Metrics](https://datatopics.worldbank.org/esg/)
'''

app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

app.layout = html.Div([
    html.Div([
        html.B('Sovereign Long Term Bond Dashboard',
               style={'font-size': '42px'}),
    ], style={'textAlign': 'center'}),

    html.Div([

        html.Div([
            html.H5('Country'),
            dcc.Dropdown(
                id='countries',
                options=[{'label': i, 'value': i} for i in countries],
                value='Australia'
            )
        ]),
        html.Div([
            html.H5('Yield Curves'),
            dcc.Checklist(
                id='pred-types',
                options=[{'label': i, 'value': i} for i in pred_indicators],
                value=['Train', 'Actual', 'ARIMA', 'Exp Smooth'],
                labelStyle={'display': 'inline-block'}
            )
        ], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([
            html.H5('Year (Credit Rating and ESG Metrics)'),
            dcc.Dropdown(
                id='data-year',
                options=[{'label': i, 'value': i} for i in explore_years],
                value='2018'
            )
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ], style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': 'rgb(250, 250, 250)',
        'padding': '20px 20px 20px 20px'
    }),

    html.Div([
        html.Div([
            html.Div([
                dcc.Graph(
                    id='yield-graph',
                )
            ], className='six columns'),

            html.Div([
                dcc.Graph(
                    id='credit-rating'
                )
            ], className='six columns'),
        ], className='row'),

        html.Div(dcc.RangeSlider(
            id='year-slider',
            min=full_table['Date'].min().year,
            max=full_table['Date'].max().year,
            value=[full_table['Date'].min().year, full_table['Date'].max().year],
            marks={str(year): str(year) for year in np.arange(full_table['Date'].min().year, full_table['Date'].max().year+1,3)},
            step=1
        ), style={'width': '40%', 'display': 'inline-block', 'padding': '0px 20px 20px 20px'}),

    ]),

    html.Div([
        html.H6('ESG Metrics', style={'padding-left': '2%'}),
        html.Div(id='esg-table-1', style={'width': '46%', 'float': 'left',
                                          'padding-left': '2%', 'display': 'inline-block'}),
        html.Div(id='esg-table-2', style={'width': '46%', 'float': 'right',
                                          'padding-right': '2%', 'display': 'inline-block'}),
        html.Div(style={'padding-bottom': '2%'})
    ], className='row'),

    html.Div([
        html.Div(
            dcc.Markdown(my_text),
            style={'padding-left': '2%'}
        )
    ], className='row')

    # Add data sources and report (copy with no GT identifiers)
    # Put on github
])


@app.callback(
    Output('yield-graph', 'figure'),
    [Input('countries', 'value'),
     Input('pred-types', 'value'),
     Input('year-slider', 'value')])

def update_yield_graph(country, preds, slider_range):
    # Get year range from slider
    year_min, year_max = slider_range
    year_min = datetime.datetime(year_min,1,1)
    year_max = datetime.datetime(year_max,12,31)
    # Filter data by year range and type of prediction graphed
    mask = (full_table['Date'] > year_min) & (full_table['Date'] < year_max) & (
    full_table['Country'] == country) & (full_table['Pred Type'].isin(preds))
    # Create graph
    fig = px.line(full_table[mask], x="Date", y="Yield", color="Pred Type")
    fig.update_layout(title='Long Term Bond Yield', xaxis_title='Year', margin=dict(l=30, r=150, t=50, b=50))
    return fig

@app.callback(
    Output('credit-rating', 'figure'),
    [Input('countries', 'value'),
     Input('data-year', 'value')])

def update_sp_graph(country, year):
    # Force year to string
    year = str(year)
    # Extract specified rating
    sp_filtered = credit.loc[credit['Country'] == country]
    cur_rating = sp_filtered.loc[sp_filtered['Year'] == int(year)]
    # Check if there is a rating for the given year, if not return alternate message
    if len(cur_rating) > 0:
        alp_rating = cur_rating['Rating'].to_numpy()[0]
        num_rating = cur_rating['Num Rating'].to_numpy()[0]
        t_size = 60
    else:
        alp_rating = 'No rating available'
        num_rating = -10
        t_size = 24
    # Create false graph to overlay text onto
    fig = go.Figure(layout={'xaxis': {'visible': False}, 'yaxis': {'visible': False}})
    fig.add_annotation(xref='paper', yref='paper', x=0.5, y=0.5, text=alp_rating,
                       font=dict(family='Times New Roman', size=t_size, color='#000000'), showarrow=False)
    title = 'Credit Rating for ' + country + ' as of Q4 in ' + year
    fig.update_layout(title=title, margin=dict(l=30, r=150, t=50, b=50))
    # Change background color according to rating
    if num_rating > 16:
        fig.update_layout(plot_bgcolor='#93C572')
    elif num_rating > 7:
        fig.update_layout(plot_bgcolor='#FFDB58')
    elif num_rating > 2:
        fig.update_layout(plot_bgcolor='#E97451')
    elif num_rating > -1:
        fig.update_layout(plot_bgcolor='#E34343')
    else:
        fig.update_layout(plot_bgcolor='#D3D3D3')
    return fig

@app.callback(
    [Output('esg-table-1', 'children'),
     Output('esg-table-2', 'children')],
    [Input('countries', 'value'),
     Input('data-year', 'value')])

def update_table(country, year):
    # Force year to string
    year = str(year)
    # Filter ESG data
    esg_filtered = esg[['Country', 'Indicator Name', year]].copy()
    esg_filtered = esg_filtered.loc[esg_filtered['Country'] == country]
    esg_filtered.drop(['Country'], axis =1, inplace = True)
    esg_filtered.rename(columns={year: 'Value'}, inplace=True)
    # Split table in half
    split_ind = len(esg_filtered)//2 + 1
    esg_1 = esg_filtered[:split_ind]
    esg_2 = esg_filtered[split_ind:]
    # Format tables to dash datatable
    esg_cols = [{'name':i, 'id':i} for i in esg_filtered.columns]
    esg_dict_1 = esg_1.to_dict('records')
    esg_dict_2 = esg_2.to_dict('records')
    # Format table display
    display = {'whiteSpace': 'normal', 'height': 'auto'}
    return (dtable.DataTable(data=esg_dict_1, columns=esg_cols, style_data=display),
            dtable.DataTable(data=esg_dict_2, columns=esg_cols, style_data=display))


if __name__ == '__main__':
    app.run_server(debug=True)


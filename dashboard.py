import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_table # for the chart
import pandas as pd # for the chart
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt
from datetime import datetime, timedelta, date
from threading import Timer
import _thread
import time

import db_operations
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# ------   purchase_history_table   ------
# cnl_column | qty | price_bought | date_column
# BitCoin    |  2  |   7680       |  2019-08-20T23:28:06.190Z
# cardano    | 500 |   0.04       |  2019-08-20T23:28:06.190Z

long_name_crypto_name_list=['Bitcoin', 'XRP', 'Monero', 'Cardano']
short_name_crypto_name_list=['BTC','XRP','XMR','ADA']
#chart data:
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')
graph_colors = ["#9962D1", "#5FDDBD", "#C96652", "#6791D3"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#1E2130', #1E2130
    'background_element' : '#161827', #161827
    'text': '#7FDBFF',
    'yellow': '#f4d44d',
    'fucia':'#92e0d3',
    'white': '#ffffff',
    'black': '#000000'
}

tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderTop': '1px solid '+colors['background_element'],
    'borderBottom': '8px solid '+colors['background_element'],
    'borderLeft':colors['background_element'],
    'borderRight':colors['background_element'],
    'backgroundColor': colors['background_element'],
    'color': 'white',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid '+colors['background_element'],
    'borderBottom': '8px solid '+colors['fucia'],
    'borderLeft':colors['background_element'],
    'borderRight':colors['background_element'],
    'backgroundColor': colors['background_element'],
    'color': 'white',
    'fontWeight':'bold',
    'padding': '6px'
}

graph_style = {
    'plot_bgcolor': colors['background_element'],
    'paper_bgcolor': colors['background_element'],
    "showlegend": True,
    'font': {
        'color': colors['white']
        }
}
graph_bar_style = {
    'plot_bgcolor': colors['background_element'],
    'paper_bgcolor': colors['background_element'],
    "showlegend": False,
    'font': {
        'color': colors['white']
        }
}

ooc_piechart_outer = {
    'height': 100,
    'margin': 0,
    'borderLeft': '#1E2130 solid 0.8rem',
    'flex': '1 1 auto',
}

top_section_container = {
    'height': '40rem',
    'flex-direction': 'row',
    'display': 'flex',
    'max-width': '100',
}

ooc_piechart_outer = {
    'border-left': 'none',
}

metric_summary_session = {
    'height': '100',
    'flex': '1 1 auto'
}

section_banner = {
    'color': 'darkgray',
    'fontSize': '1.5rem',
    'textAlign': 'left',
    'padding': '1rem 2rem',
    'borderBottom': '1px solid #4b5460'
}

date_picker_style = {
    'color': 'darkgray',
    'textAlign': '1.5rem'
}



def generate_section_banner(title):
    return html.Div(className="section_banner", children=title)
def generate_piechart():
    pie_colors=[]
    i=0
    labels=db_operations.query_database('purchase_history_table',['currency_name_short'],False, None)
    values_crypto_qty=[]
    values_price_per_coin=[]
    for label in labels:
        values_crypto_qty.append(db_operations.query_database('purchase_history_table', ['quantity_of_currency_acquired'], False, label)[0])   # quantity of crypto
        values_price_per_coin.append(db_operations.query_database('purchase_history_table', ['CAD_price_latest'], False, label)[0])           #latest price
        pie_colors.append(graph_colors[i])
        i=i+1
        if i>=len(graph_colors):
            i=0
    values=[]
    values=[c*d for c,d in zip(values_crypto_qty,values_price_per_coin)]
    if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] GENERATE_PIECHART [ values ]  :",values)

    return dcc.Graph(
        id="piechart",
        figure={
            "data": [
                {
                    "labels": labels,
                    "values": values,
                    "type": "pie",
                    "marker": {"colors": pie_colors, "line": {"color": "white", "width": 4}},
                    "hoverinfo": "label",
                    "textinfo": "label",
                }
            ],
            "layout": {
                "margin": dict(l=20, r=20, t=20, b=20),
                "uirevision": True,
                "showlegend": True,
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": colors['black']},
                "autosize": True,
            },
        },
    )

def generate_datepicker():
    today_date=dt.today().strftime('%Y,%m,%d')
    year=int(today_date[0:4])
    month=int(today_date[5:7])
    day=int(today_date[8:10])

    return html.Div(
        id="output-container-date-picker-single",
        children=[
            html.Label(id="metric-select-title", children="Select the acquisition date"),
            dcc.DatePickerSingle(
                id="date-picker-single",
                min_date_allowed=dt(2018,1,1),
                date=dt(year, month, day), #format 2019,1,1
                with_portal=True
            ),
        ])
def total_folio_value():
    total_asset_list=[]
    total_profit_list=[]
    value_latest=db_operations.query_database('purchase_history_table', ['CAD_price_latest'], False, None)
    print("Value latest: ", value_latest)
    value_purchase=db_operations.query_database('purchase_history_table', ['CAD_price_at_purchase'], False, None)
    print("Value value_purchase: ", value_purchase)
    total_coin=db_operations.query_database('purchase_history_table', ['quantity_of_currency_acquired'], False, None)
    print("Value latest: ", total_coin)
    test=db_operations.query_database('purchase_history_table', ['price_variation'], False, None)
    profit=[value_latest_i - value_purchase_i for value_latest_i, value_purchase_i in zip(value_latest, value_purchase)]
    print("Value profits: ", profit)
    for id, column in enumerate(value_latest):
        if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] total_folio_value []: ID: ",id," value: ",column," latest value ",value_latest[id]," value fluctuation ",profit[id]," portfolio value: ",value_latest[id]*total_coin[id], " folio Gain: ",profit[id]*total_coin[id])
        total_asset_list.append(value_latest[id]*total_coin[id])
        total_profit_list.append(profit[id]*total_coin[id])

    if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] total_folio_value []: Total profits: ",sum(total_profit_list))
    if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] total_folio_value []: Total value  : ",sum(total_asset_list))
    total_asset="{0:.2f}".format(sum(total_asset_list))
    total_profit="{0:.2f}".format(sum(total_profit_list))
    secondline="You have "+str(total_asset)
    if sum(total_profit_list) > 0:
        finalline="Up "+str(sum(test))
    else:
        total_profit="{0:.2f}".format(-1*sum(total_profit_list))
        finalline="Down "+str(total_profit)

    return html.Div(children=[
        html.H1(
            'Welcome',
            style={
                'textAlign':'center',
                'color':colors['yellow'],
            },
        ),
        html.H2(
            secondline,
            style={
                'textAlign':'center',
                'color':colors['yellow'],
            },
        ),html.H2(
            finalline,
            style={
                'textAlign':'center',
                'color':colors['yellow'],
            },
        )
    ])

app.layout = html.Div(style={'backgroundColor':colors['background']}, children=[
    # Title
    # html.H1(
    #     'Cryptocurrency portofolio',
    #     style={
    #         'textAlign':'center',
    #         'color':colors['yellow'],
    #     },
    # ),
    total_folio_value(),
    # Graphs w/ tabs
    dcc.Tabs(id="tabs-exemple", value='tab-1-example', children=[
        dcc.Tab(label='Assets by weight', value='tab-1-example', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Historical data', value='tab-2-example', style=tab_style, selected_style=tab_selected_style),
    ], style=tabs_styles),
    html.Div(id='tabs-content-example'),

    html.Div(
        id="top_row",
        className="row",
        children=[
            html.Div(
                id="metric_summary_session",
                className="seven columns",
                children=[
                    html.H3(
                        'Your assets',
                        style={
                            'textAlign':'center',
                            'color':colors['yellow'],
                            'backgroundColor':colors['background_element']
                            },
                    ),

                    dcc.Dropdown(
                    id="variation_price_picker",
                        options=[
                            {"label": "Last 7 days", "value": "-7 day"},
                            {"label": "Last month", "value": "-30 day"},
                            {"label": "Last 6 month", "value": "-180 day"},
                            {"label": "All", "value": "all"}
                        ],
                        value="all",
                    ),
                    dcc.Store(id="selected_variation_price", storage_type="memory"),
                    dcc.Store(id="selected_columns", storage_type="memory"),
                    html.Div(id="my-tables-container")
                ]
            ),
            html.Div(
                id="ooc_piechart_outer",
                className="five columns",
                style={"height": "100%"},
                children=[
                    html.H3(
                        'Portfolio',
                        style={
                            'textAlign':'center',
                            'color':colors['yellow'],
                            'backgroundColor':colors['background']
                            },
                    ),
                    generate_piechart(),
                ]
            )
        ],
    ),
    #Type of currency bought
    html.Div( # whole bottom line for a title
        id="bottom_row",
        className="row",
        children=[
        html.Div(
            id="bottom_row_left_column",
            className="four columns",
            children=[
                html.H3(
                'Form to add asset',
                style={
                    'textAlign':'center',
                    'color':colors['yellow'],
                    'backgroundColor':colors['background_element']
                },
            ),
        ]),
    ]), # whole bottom line for a title - end



    html.Div( # new row under title
        id="bottom_row_2",
        className="row",
        children=[
            html.Div( # left side
                id="crypto_picker",
                className="two columns",
                children=[
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id="currency_picker",
                            options=[
                                {'label': 'BitCoin [BTC]','value':short_name_crypto_name_list[0]},
                                {'label': 'Ripple [XRP]', 'value': short_name_crypto_name_list[1]},
                                {'label': 'Cardano [ADA]','value': short_name_crypto_name_list[3]}
                            ],placeholder="Select a currency",
                        ),
                        #html.Div(id='currency-dropdown-output-container'),
                    ]),
                html.Br(),
                generate_datepicker()
            ]), #top left corner - end

            html.Div( # right side
                id="crypto_picker_right",
                className="two columns",
                children=[
                    html.Div( # right COLUMN
                    children=[ # right side
                        html.Div(dcc.Input(id='acquisition-price-box', type='text', placeholder='acquisition price [CAD]')),
                    ],
                    style={
                        'textAlign':'left',
                        'color':colors['yellow'],
                        'backgroundColor':colors['background_element']
                        },
                    ), # right side - end
                    html.Br(),
                    html.Br(),
                    html.Div( # right COLUMN
                    children=[ # right side
                        html.Div(dcc.Input(id='amount-acquired-box', type='text', placeholder='amount acquired'))
                    ],
                    style={
                        'textAlign':'left',
                        'color':colors['yellow'],
                        'backgroundColor':colors['background_element'],
                        },
                    ), # right side - end
                ]),
    ]),
    html.Div( # new row under the add stuff to submit changes
        id="bottom_row_full",
        className="row",
        children=[
            html.Div(
                id="left_final_row",
                className="four columns",
                children=[
                    html.Div([
                    dcc.ConfirmDialogProvider(
                        children=html.Button('Save to database'),
                        id='save-to-database-button',
                        message='This will be saved to the database. Sure?',
                        )
                    ]),
                ],
                style={
                    'textAlign':'center',
                    'color':colors['yellow'],
                    'backgroundColor':colors['background_element']
                    }
            )],
    ),
    html.Div(
        id='new_purchase_status',
        style={
            'textAlign':'center',
            'color':colors['yellow'],
            'backgroundColor':colors['background_element']
            }
    )
])


@app.callback(
# to DOS
    # https://community.plot.ly/t/multiple-outputs-in-dash-now-available/19437
        [dash.dependencies.Output('new_purchase_status', 'children')
        ],
        [dash.dependencies.Input('save-to-database-button', 'submit_n_clicks')],
        [dash.dependencies.State('currency_picker', 'value'),
        dash.dependencies.State('date-picker-single', 'date'),
        dash.dependencies.State('acquisition-price-box','value'),
        dash.dependencies.State('amount-acquired-box','value')]
        )
def update_output(submit_to_db_button, currency_picker, date,acquisition_price_input, amount_acquired_input):
    global write_to_database_list
    if submit_to_db_button:
        if date is not None:
            #YYYY-MM-DDTHH:MM:SS
            #yyyy-MM-dd'T'HH:mm:ss.SSS'Z' from : https://help.sumologic.com/03Send-Data/Sources/04Reference-Information-for-Sources/Timestamps%2C-Time-Zones%2C-Time-Ranges%2C-and-Date-Formats
            #2019-12-20T23:28:06.190Z
            if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] update_output [date is] : ",date)
            try:
                date=datetime.strptime(str(date), "%Y-%m-%d")
            except:
                date=datetime.strptime(str(date), "%Y-%m-%dT%H:%M:%S")
            date_string = date.strftime('%Y-#-#T')
            date_string = date.strftime('%B %d %Y')


            if submit_to_db_button is not None:
                columns=['currency_name_long', 'currency_name_short', 'CAD_price_at_purchase','CAD_price_latest','quantity_of_currency_acquired','acquisition_date', 'price_variation']
                data=['str','str', 0.0,0.0,'str'] #init the list with elements as they might get modified not orderly
                id=short_name_crypto_name_list.index(currency_picker)
                currency_long_name=long_name_crypto_name_list[id]
                data=[currency_long_name,currency_picker,float(acquisition_price_input),0.0,float(amount_acquired_input),date_string, 0.0]
                #Get current currency in list before adding the new one
                current_currency_list=db_operations.query_database('purchase_history_table', ['currency_name_short'], False, None)
                db_operations.write_to_database('purchase_history_table', columns, data)




            #ADD IF CURRENCY_NAME_LONG NOT IN purchase_history_table, THEN GET HISTORICAL DATA SINCE ACQUISITION DATE
            #current_currency_list=db_operations.query_database('purchase_history_table', ['currency_name_short'], False, None)
            if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] UPDATA_OUTPUT [ CURRENCY LIST ]  :",current_currency_list)
            if currency_picker not in current_currency_list:
                #get historical data
                ticker=currency_picker+'-'+db_operations.parameters['convert']
                #today = date.today()
                #end_date = date(today.year, today.month, today.day)
                end_date=date.today()
                if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] UPDATA_OUTPUT [ CURRENCY LIST ]  :",ticker)
                db_operations.Get_Historical_data(ticker, currency_picker, currency_long_name, date_string,end_date)

            return ['The purchase of {} {} for {} $ on {} has successfully been added to the database. Please reload the page.'.format(amount_acquired_input, currency_picker, acquisition_price_input, date_string)]

    else:
        return ['']

@app.callback(Output('tabs-content-example','children'),
            [Input('tabs-exemple', 'value')])
def render_content(tab):
    labels = db_operations.query_database('purchase_history_table',['currency_name_short'],False, None)

    if tab == 'tab-1-example':
        y_values=[]
        label_list=[]
        i=0
        bars_colors=[]
        for label in labels:
            if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] render_content [label] : ",label)
            quantity_of_currency=db_operations.query_database('purchase_history_table', ['quantity_of_currency_acquired'], False, label)
            if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] render_content [quantity_of_currency] : ",quantity_of_currency)
            CAD_price_latest=db_operations.query_database('purchase_history_table', ['CAD_price_latest'], False, label)
            if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] render_content [CAD_price_latest] : ",CAD_price_latest)
            y_value=quantity_of_currency[0]*CAD_price_latest[0]
            y_values.append("{0:.2f}".format(y_value))
            label_list.append(label)
            bars_colors.append(graph_colors[i])
            i=i+1
            if i>=len(graph_colors):
                i=0

        fig = go.Figure()
        fig.add_trace(go.Bar(x=label_list, y=y_values, name=label,marker={'color':bars_colors}))
        fig.update_layout(graph_bar_style)

        return html.Div([
            html.H3(
                'Assets',
                style={
                    'textAlign':'center',
                    'color':colors['yellow'],
                    'backgroundColor':colors['background_element']
                    },
            ),
            dcc.Graph(
                id='graph-1-tabs',
                figure=fig
            )
        ])
    elif tab == 'tab-2-example':
        x_dates=[]
        y_values=[]
        label_list=[]
        bar_colors=[]
        times=['7 day', '1 month', '6 months', 'All']
        for label in labels:
            results=db_operations.query_database('historical_data_table', ['timestamp_strftime'], False, label)
            for result in results:
                label_list.append(label)
                x_dates.append(result)

            results=db_operations.query_database('historical_data_table', ['CAD_price'], False, label)
            qty_acq=db_operations.query_database('purchase_history_table', ['quantity_of_currency_acquired'], False, label)
            date_acq=db_operations.query_database('purchase_history_table', ['acquisition_date'], False, label)
            temp_date_acq=[]
            for date in date_acq:
                temp_date_acq.append(datetime.strptime(date, '%B %d %Y'))
            i=0
            sum=0
            if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] GET_PRICE_VARIATION [Quantity acquired]: ", qty_acq)
            if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] GET_PRICE_VARIATION [Date acquired]: ", date_acq)

            for result in results:
                print(x_dates[i])
                if datetime.strptime(x_dates[i], '%Y-%m-%d') in temp_date_acq:
                    if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] GET_PRICE_VARIATION [Date specified]: ", datetime.strptime(x_dates[i], '%Y-%m-%d'))
                    if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] GET_PRICE_VARIATION [indexes]: ", temp_date_acq)
                    indexes=[i2 for i2,v in enumerate(temp_date_acq) if v<=datetime.strptime(x_dates[i], '%Y-%m-%d')] # get indexes of date_acq where date of list is larger (past) date qty_acquired
                    if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] GET_PRICE_VARIATION [indexes]: ", indexes)
                    if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] GET_PRICE_VARIATION [quantity list]: ", qty_acq)
                    sum=0
                    for temp_indexes in indexes:
                        sum=sum+qty_acq[temp_indexes]
                        if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] GET_PRICE_VARIATION [Sum]: ", sum)
                    if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] GET_PRICE_VARIATION [Final Sum --> ]: ", sum)
                if sum==0:
                    sum=qty_acq[0]
                y_value=result*sum
                #y_value=result*qty_acq[0]
                y_values.append("{0:.2f}".format(y_value))
                i=i+1
            print(label)
            print(len(y_values))
            print(len(x_dates))
        for y,x in zip(y_values,x_dates):
            print("Y: "+str(y)+"|  Date: "+ str(x))

        fig = px.line(dict(Currency=label_list, Value=y_values, time=x_dates), x='time', y='Value', color='Currency')
        fig.update_traces(mode='markers+lines')
        fig.update_layout(graph_style)

        return html.Div([
            html.H3(
                'Historical data',
                style={
                    'textAlign':'center',
                    'color':colors['yellow'],
                    'backgroundColor':colors['background_element'],
                    },
            ),
            dcc.Graph(
                id='graph-2-tabs',
                figure=fig
            )
        ])

@app.callback(
    [dash.dependencies.Output("selected_variation_price", "data"),
    dash.dependencies.Output("selected_columns", 'data')],
    [dash.dependencies.Input("variation_price_picker", "value")],
    [dash.dependencies.State("selected_variation_price", "data")],
    #dash.dependencies.State("selected_columns", 'data')],
)
def display_output(value, variation_time_period):
    if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] DISPLAY_OUTPUT [picker]: ",value)
    if value is not None:
        # get price since value from historical_data_table
        db_operations.get_price_variation(value)
        # save return value to purchase_history_table
        # get values from wanted column (hard coded sqlite function)
        columns=[]
        columns=db_operations.get_columns('purchase_history_table')
        # find and replace column names with readable values
        for id, column in enumerate(columns):
            if column == 'currency_name_long':
                columns[id]='Currency'
            elif column == 'CAD_price_at_purchase':
                columns[id]='Price at purchase'
            elif column == 'CAD_price_latest':
                columns[id]='Latest Price'
            elif column == 'quantity_of_currency_acquired':
                columns[id]='Quantity of coins owned'
            elif column == 'acquisition_date':
                columns[id]='Date acquired'
            elif column == 'price_variation':
                columns[id]='Price variation since {selection}'.format(selection=value)

        # remove element containing '_' from column list
        columns=[ x for x in columns if "_" not in x ]
        data=db_operations.query_database('purchase_history_table', ['currency_name_long','CAD_price_at_purchase','CAD_price_latest', 'quantity_of_currency_acquired','acquisition_date', 'price_variation'], True, None)
        return({"selected_rows":data},{"selected_columns":columns})


@app.callback(
    Output("my-tables-container", "children"),
    [Input("selected_variation_price", "data"), Input("selected_columns", "data")],
)
def update_graph(variation_price, columns):
    if columns is None:
        if db_operations.DEBUG_FLAG is True: print("[",db_operations.lineno(),"] UPDATE_GRAPH None type detected")
        return
    #print("UPODATE_GRAPH [variation_price] : ", variation_price)
    _df = variation_price["selected_rows"]
    cols = columns["selected_columns"]

    for id, dict in enumerate(_df):
        keys = [*dict]
        for key in keys:
            if key == 'currency_name_long':
                dict['Currency'] = dict.pop('currency_name_long')
            elif key == 'CAD_price_at_purchase':
                dict['Price at purchase'] = dict.pop('CAD_price_at_purchase')
            elif key == 'CAD_price_latest':
                dict['Latest Price'] = dict.pop('CAD_price_latest')
            elif key == 'quantity_of_currency_acquired':
                dict['Quantity of coins owned'] = dict.pop('quantity_of_currency_acquired')
            elif key == 'acquisition_date':
                dict['Date acquired'] = dict.pop('acquisition_date')
            elif key == 'price_variation':
                dict[str(cols[-1])] = dict.pop('price_variation')

    return html.Div(
            children=dash_table.DataTable(
            #id='dynamic-table',
            columns=[{"name":i,"id":i} for i in cols],
            data=_df,
            #columns=[{"name":i, "id": i} for i in db_operations.get_columns('purchase_history_table')], # output a list of column name
            #data=db_operations.query_database('purchase_history_table', db_operations.get_columns('purchase_history_table'), True, None),
            style_as_list_view=True,
            style_header={'backgroundColor':colors['background'], 'color':colors['yellow'], 'textAlign':'center'},
            style_cell={
                'backgroundColor':colors['background'],
                'color': 'white',
                'textAlign':'center',
            },
            page_action="native",
            page_current= 0,
            page_size= 8,
        )
    )

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)

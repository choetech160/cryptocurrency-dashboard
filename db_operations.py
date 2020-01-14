import sqlite3
import json
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import datetime
import dict_example

import inspect # for debbuging, get code line number

# ONLY USED FOR Create_Historical_data [CAN BE COMMENTED ONCE YOU GOT THE HISTORICAL DATA]
import pandas_datareader.data as web
import datetime
import pandas as pd
import API_data
# ONLY USED FOR Create_Historical_data

DEBUG_FLAG = True # will output the line number, the function name and the variable value.
# API For coinmarketcap parameters
latest_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': API_data.api,
}
parameters = {
  'start':'1',
  'limit':'20',
  'convert':'CAD'
}
# Database parameters
sqlite_file='/Users/home/Desktop/Projets/local_dashboard/database.sqlite'
#sqlite_file='/Users/temp/Desktop/Projects/dashboard/database_demo.sqlite'
historical_data_table='historical_data_table'
purchase_history_table='purchase_history_table'

cnl_column='currency_name_long'
cns_column='currency_name_short'
price_column='CAD_price'
date_column='timestamp'
# ------   historical_data_table   ------
# currency_name_long | currency_name_short | CAD_price | timestamp_readable | timestamp_strftime
# Bitcoin            | BTC	               | 7202.55   | January 02 2020    | 2020-01-02
# Bitcoin	         | BTC	               | 7194.89   | January 01 2020    | 2020-01-01
# Bitcoin	         | BTC	               | 7294.44   | December 31 2019   | 2019-12-31
# Bitcoin	         | BTC	               | 7420.27   | December 30 2019   | 2019-12-30
# Bitcoin	         | BTC	               | 7317.65   | December 29 2019   | 2019-12-29
#  ...               | ...                 | ...       | ...

acq_date='acquisition_date'
qty='quantity_of_currency'
price_bought='price_per_coin_cad'

# ------   purchase_history_table   ------
# currency_name_long | currency_name_short | CAD_price_at_purchase | CAD_price_latest | quantity_of_currency_acquired | acquisition_date
# XRP	             | XRP	               | 0.256892	           | 0.196587	      | 250	                          | November 11 2019
# Bitcoin	         | BTC	               | 8567.62	           | 7658.25	      | 0.004	                      | November 13 2019

def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno

def create_table(table_name, column, field_type):
    # Used to create tables and columns as the fct does the appropriate checks
    # Input  : table_name (str), column (column name as str), field_type (type=> 'TEXT', 'INTEGER')
    # Output : none

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    # Verify if table exist or not
    c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{tn}' '''.format(tn=table_name))


    if c.fetchone()[0]==1 : #table exists
       # Modify table
       c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='column' AND name='{nf}' '''.format(nf=column))

       if c.fetchone()[0]==1 :
           if DEBUG_FLAG is True: printf("Column {nf} already exist in table {tn}".format(mf=column, tn=table_name))
       else:
           c.execute("ALTER TABLE {tn} ADD COLUMN '{nf}' {ft}"\
               .format(tn=table_name, nf=column, ft=field_type))
    else : #table does not exists
       c.execute('CREATE TABLE IF NOT EXISTS {tn} ({nf} {ft})'\
           .format(tn=table_name, nf=column, ft=field_type))

    conn.commit()
    conn.close()

def modify_table(table_name, column, value, currency):
    # table_name : table to modify
    # column : column to modify
    # value : the new value that will be written over the previous one
    # currency : the currency that have to be changed (short name)
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    if DEBUG_FLAG is True: print("[",lineno(),"] MODIFY_TABLE [value]  :",value)
    if DEBUG_FLAG is True: print("[",lineno(),"] MODIFY_TABLE [column] :",column)
    #columns_cmd = ', '.join(map(str, column))
    data_cmd=str(value).replace('[','').replace(']','')
    #print(columns_cmd)
    if DEBUG_FLAG is True: print("[",lineno(),"] MODIFY_TABLE [data as str for next command] :",data_cmd)
    command = "UPDATE "+table_name+" SET "+column+" = "+data_cmd+" WHERE currency_name_short LIKE '"+currency+"'"
    if DEBUG_FLAG is True: print("[",lineno(),"] MODIFY_TABLE [SQLITE COMMAND] :",command)
    c.execute(command)
    conn.commit()
    conn.close()

    return

def write_to_database(table_name, columns, data):
    #
    # Input : table_name(str), columns (list of columns), data (line of data per column to insert)
    # Output: none
    # 2019-12-20T23:28:06.190Z
    # YYYY-MM-DDTHH:MM:SS.????

    columns_cmd = ', '.join(map(str, columns))
    data_cmd=str(data).replace('[','').replace(']','')
    command = "INSERT INTO "+table_name+" ("+columns_cmd+") VALUES ("+data_cmd+")"
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    if DEBUG_FLAG is True: print("[",lineno(),"] WRITE_TO_DATABASE [command]  :",command)
    c.execute(command)
    #except sqlite3.IntegrityError:
    #    print('ERROR: ID already exists in PRIMARY KEY column {}'.format(command))
    conn.commit()
    conn.close()
    if DEBUG_FLAG is True: print("[",lineno(),"] WRITE_TO_DATABASE [DONE]")
    return

def query_database(table_name, columns, graph_flag, crypto_name):
    # Graph_flag : when creating a graph, the result must have a specific format. The flag is used only to
    #               re-create that specific format [{column_name}, value]
    # columns : list of columns to get (MUST be a list)

    columns_cmd=', '.join(map(str, columns))
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    if graph_flag is True and crypto_name is None:
        command="SELECT "+columns_cmd+" FROM "+table_name
        if DEBUG_FLAG is True: print("[",lineno(),"] QUERY_DATABASE() [SQLITE COMMAND] :",command)
        c.execute(command)
        rows = c.fetchall()
        list_dict=[]
        i=0
        for row in rows:
            row_dict={}
            if DEBUG_FLAG is True: print("[",lineno(),"] QUERY_DATABASE() [row] => ", row)
            for column_element in row:
                try:
                    if column_element == row[3]:
                        row_dict[columns[i]]=column_element
                    else:
                        column_element='{:,.2f}$'.format(column_element)
                        row_dict[columns[i]]=column_element
                except:
                    row_dict[columns[i]]=column_element
                i=i+1
            list_dict.append(row_dict)
            i=0
        conn.close()
        return list_dict

    elif graph_flag is False and crypto_name is None:
        command="SELECT "+columns_cmd+" FROM "+table_name
        #print('QUERY_DATABASE: command =≥ ', command)
        c.execute(command)
        rows = c.fetchall()
        list_dict=[]
        for row in rows:
            list_dict.append(row[0])
        conn.close()
        return list_dict

    elif graph_flag is False and crypto_name is not None:
        if 'timestamp_strftime' in columns or 'CAD_price' in columns:
            command="SELECT "+columns_cmd+" FROM "+table_name+" WHERE currency_name_short LIKE '"+crypto_name+"' ORDER BY strftime(timestamp_strftime)"
        else:
            command="SELECT "+columns_cmd+" FROM "+table_name+" WHERE currency_name_short LIKE '"+crypto_name+"'"
        c.execute(command)
        rows = c.fetchall()
        list_dict=[]
        for row in rows:
            list_dict.append(row[0])
        conn.close()
        return list_dict
    else:
        if DEBUG_FLAG is True: print("[",lineno(),"] MODIFY_TABLE [SQLITE COMMAND] :",print("error, no status!!"))
        conn.close()

def get_columns(table_name):
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    c.execute("SELECT * FROM {tn} where 1=0".format(tn=table_name))
    return [d[0] for d in c.description]

def get_data():
    # should be run every 24hours to add new data to the database
    # Get the data from the API
    session = Session()
    session.headers.update(headers)
    try:
      response = session.get(latest_url, params=parameters)
      data = json.loads(response.text)

    except (ConnectionError, Timeout, TooManyRedirects) as e:
      print(e)

    data_dict=data["data"]
    #data_dict=dict_example.my_dict["data"]
    # get currency by long name (list)
    currency_list = query_database('purchase_history_table', [cns_column], False, None)
    # all asset in a list
    data=['str','str','str','str', 'str'] #init the list with elements as they might get modified not orderly
    for currency_symbol in currency_list:
        for i in range(len(data_dict)):
            if data_dict[i]["symbol"] == currency_symbol:
                data[0]=data_dict[i]["name"]
                data[1]=data_dict[i]["symbol"]
                for d_id in data_dict[i]["quote"]["CAD"]:
                    if d_id == "price":
                        data[2]=data_dict[i]["quote"]["CAD"][d_id]
                    elif d_id == "last_updated":
                        date = data_dict[i]["quote"]["CAD"][d_id]
                        date=datetime.datetime.strptime(data_dict[i]["quote"]["CAD"][d_id], "%Y-%m-%dT%H:%M:%S.%fZ")
                        date_string = date.strftime('%Y-#-#T')
                        date_string = date.strftime('%B %d %Y')
                        date_strformat=datetime.datetime.strptime(date_string,"%B %d %Y")
                        date_strformat=date.strftime('%Y-%m-%d')
                        data[3]=date_string
                        data[4]=date_strformat
                #print(*data, sep=" | ")
                columns=['currency_name_long', 'currency_name_short', 'CAD_price', 'timestamp', 'timestamp_strftime']
                write_to_database('historical_data_table', columns, data)
                modify_table('purchase_history_table', 'CAD_price_latest', data[2], data[1])
    return

def get_price_variation(variation_period):
    # check currency in purchase_history_table
    currency_list = query_database('purchase_history_table', [cns_column], False, None)
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    # use that to check historical price data
    if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [list]: ",currency_list)
    for currency_symbol in currency_list:
        if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [SYMBOL]: ", currency_symbol)
        if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [VARIATION PERIOD]: ", variation_period)
        if variation_period == 'all':
            variation_period_value=query_database('purchase_history_table',['acquisition_date'], False, currency_symbol) # get date of purchase of specific currency
            if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [variation period]: ", variation_period_value)
            date_format_from_db = "%B %d %Y"
            today = datetime.date.today()
            a = datetime.datetime.strptime(variation_period_value[0], date_format_from_db) #['November 11 2019']
            b = datetime.datetime.strptime(str(datetime.date.today()),"%Y-%m-%d")
            delta = b - a
            variation_period_value="-"+str(delta.days)+" day"
            if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [variation period]: ", variation_period_value)
        else:
            variation_period_value=variation_period



        #print('GET_PRICE_VARIATION[variation]: ',date_format_from_db)
        # get price since the time period selected by user (7 days, one month etc)
        command="SELECT CAD_price FROM historical_data_table WHERE timestamp_strftime IS strftime('%Y-%m-%d','now', '"+str(variation_period_value)+"') AND currency_name_short LIKE '"+currency_symbol+"'"
        if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [SQLITE COMMAND]: ", command)
        c.execute(command)
        variation_price = c.fetchall()
        try:
            variation_price=variation_price[0][0]
        except:
            variation_period_value=query_database('purchase_history_table',['acquisition_date'], False, currency_symbol)
            date_format_from_db = "%B %d %Y"
            today = datetime.date.today()
            a = datetime.datetime.strptime(variation_period_value[0], date_format_from_db) #['November 11 2019']
            b = datetime.datetime.strptime(str(datetime.date.today()),"%Y-%m-%d")
            delta = b - a
            variation_period_value="-"+str(delta.days)+" day"
            command="SELECT CAD_price FROM historical_data_table WHERE timestamp_strftime IS strftime('%Y-%m-%d','now', '"+str(variation_period_value)+"') AND currency_name_short LIKE '"+currency_symbol+"'"
            c.execute(command)
            variation_price=c.fetchall()
            variation_price=variation_price[0][0]

        # Get latest price
        command="SELECT CAD_price FROM historical_data_table WHERE timestamp_strftime IS strftime('%Y-%m-%d','now') AND currency_name_short LIKE '"+currency_symbol+"'"
        if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [SQLITE COMMAND]: ", command)
        c.execute(command)
        latest_price = c.fetchall()
        latest_price=latest_price[0][0]

        command="SELECT quantity_of_currency_acquired FROM purchase_history_table WHERE currency_name_short LIKE '"+currency_symbol+"'"
        if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [SQLITE COMMAND]: ", command)
        c.execute(command)
        qty_acquired = c.fetchall()
        qty_acquired=qty_acquired[0][0]
        if DEBUG_FLAG is True: print('-'*200)
        if DEBUG_FLAG is True: print("[",lineno(),"] Currency: ",currency_symbol)
        if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [latest_price]: ",latest_price)
        if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [qty_acquired]: ",qty_acquired)
        if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [variation_price]: ",variation_price)
        if DEBUG_FLAG is True: print('-'*200)
        var=(latest_price-variation_price)*qty_acquired
        var='{:,.2f}'.format(var)
        # save each value in purchase_history_table
        command="UPDATE purchase_history_table SET price_variation = "+str(var)+" WHERE currency_name_short LIKE '"+currency_symbol+"'"
        if DEBUG_FLAG is True: print("[",lineno(),"] GET_PRICE_VARIATION [SQLITE COMMAND]: ", command)
        c.execute(command)
        conn.commit()

    return

def Get_Historical_data(ticker, short_name, long_name, start_date, end_date):
    data=['str','str',0.0,'str', 'str']
    data[0]=long_name
    data[1]=short_name
    if DEBUG_FLAG is True: print("[",lineno(),"] GET_HISTORICAL_DATA [data]  :",data)
    df=web.DataReader(ticker,'yahoo',start_date,end_date)
    if DEBUG_FLAG is True: print("[",lineno(),"] GET_HISTORICAL_DATA [data - head]  :",df.head)
    #                  High        Low       Open      Close     Volume  Adj Close
    # Date
    # 2019-11-09  62.482334  60.667355  60.843990  62.182247  150673894  62.182247
    # 2019-11-10  64.551414  61.982513  62.212288  63.902664  176219413  63.902664
    # 2019-11-11  64.218246  61.438305  63.891048  61.929924  206142758  61.929924
    # 2019-11-12  65.741707  61.877323  61.933327  62.257629  188591183  62.257629
    # 2019-11-13  65.706177  62.112125  62.252892  65.330238  208429249  65.330238

    opening=df['Open']
    all_weekdays=pd.date_range(start=start_date, end=end_date, freq='D') #D = all days, B = business days
    #opening=opening.reindex(all_weekdays)
    #opening=opening.fillna(method='ffill')
    date_list=[]
    temp=[]
    i=0
    for day in all_weekdays:
        day=day.strftime("%Y-%m-%d")
        temp=[day, opening[i]]
        date_list.append(temp)
        i=i+1

    columns=['currency_name_long', 'currency_name_short', 'CAD_price', 'timestamp', 'timestamp_strftime']
    for date,value in date_list:
        data[2]=float(value)
        data[4]=date
        date=datetime.datetime.strptime(date,"%Y-%m-%d")
        date_str=date.strftime('%Y-#-#T')
        date_str = date.strftime('%B %d %Y')
        data[3]=date_str
        write_to_database('historical_data_table', columns, data)
    get_data() # update all to the latest data
    return

def Create_Historical_data():
    # import pandas_datareader.data as web
    # import datetime
    # import pandas as pd
    data=['str','str',0.0,'str', 'str']
    # ----- !!!!!!  THESE VALUES NEED TO BE CHANGED MANUALLY !!!!!! -----
    # everytime the function is run, otherwise your tables will look like shit
    start_date=datetime.datetime(2019,11,9)
    end_date=datetime.datetime(2020,1,14)
    tickers=['ETH-CAD','BTC-CAD','XMR-CAD','XRP-CAD']
    short_name=['ETH', 'BTC', 'XMR', 'XRP']
    long_name=['Ethereum', 'Bitcoin', 'Monero', 'XRP']
    # start_date=datetime.datetime(2018,1,3)
    # end_date=datetime.datetime(2020,1,9)
    # tickers=['BTC-CAD','XRP-CAD']
    # short_name=['BTC', 'XRP']
    # long_name=['Bitcoin', 'XRP']

    for id, ticker in enumerate(tickers):
        if DEBUG_FLAG is True: print("[",lineno(),"] CREATE_HISTORICAL_DATA [ticker]  :",ticker)
        if DEBUG_FLAG is True: print("[",lineno(),"] CREATE_HISTORICAL_DATA [ID]  :",id)
        data[0]=long_name[id]
        data[1]=short_name[id]
        # ----- !!!!!!  THESE VALUES NEED TO BE CHANGED MANUALLY !!!!!! -----


         #init the list with elements as they might get modified not orderly
        df=web.DataReader(ticker,'yahoo',start_date,end_date)
        if DEBUG_FLAG is True: print("[",lineno(),"] CREATE_HISTORICAL_DATA [data - head]  :",df.head)
        #                  High        Low       Open      Close     Volume  Adj Close
        # Date
        # 2019-11-09  62.482334  60.667355  60.843990  62.182247  150673894  62.182247
        # 2019-11-10  64.551414  61.982513  62.212288  63.902664  176219413  63.902664
        # 2019-11-11  64.218246  61.438305  63.891048  61.929924  206142758  61.929924
        # 2019-11-12  65.741707  61.877323  61.933327  62.257629  188591183  62.257629
        # 2019-11-13  65.706177  62.112125  62.252892  65.330238  208429249  65.330238

        opening=df['Open']
        all_weekdays=pd.date_range(start=start_date, end=end_date, freq='D') #D = all days, B = business days
        #opening=opening.reindex(all_weekdays)
        #opening=opening.fillna(method='ffill')
        date_list=[]
        temp=[]
        i=0
        for day in all_weekdays:
            day=day.strftime("%Y-%m-%d")
            temp=[day, opening[i]]
            date_list.append(temp)
            i=i+1

        columns=['currency_name_long', 'currency_name_short', 'CAD_price', 'timestamp', 'timestamp_strftime']
        for date,value in date_list:
            data[2]=float(value)
            data[4]=date
            date=datetime.datetime.strptime(date,"%Y-%m-%d")
            date_str=date.strftime('%Y-#-#T')
            date_str = date.strftime('%B %d %Y')
            data[3]=date_str
            write_to_database('historical_data_table', columns, data)

    return

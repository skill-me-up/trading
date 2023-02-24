# Libraries
import opstrat as op
import pandas as pd
import requests
import json
import math
import os
from kiteconnect import KiteConnect, KiteTicker
from datetime import date
from datetime import timedelta
from datetime import datetime as dt
from datetime import time
from tradingclasses import Cap_Client, Trading
from generalclasses import General
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logging.basicConfig(level=logging.INFO)

"""-----------------------------------------------------------------------------"""
# Changing Current Working Directory
cwd = os.chdir("C:\\Users\\Yugenderan\\OneDrive\Professional Development\\Programming_Everything\\Trading")
"""-----------------------------------------------------------------------------"""

strategy = 'nap'
base_account_name = 'iampl'
base_account_broker ='zerodha'
client_data = pd.read_csv("files\\clients_list.csv", index_col='client_name')
client_data = client_data[client_data[strategy] > 0].fillna('a')
brokers = client_data['broker'].tolist()
clients = {}

for broker in brokers:
    clients[broker] = {}
    cl_data = client_data[client_data['broker'] == broker].T
    for name in cl_data:
        clients[broker][name] = Cap_Client(cl_data[name], strategy)    

base_account = clients[base_account_broker][base_account_name]
session = clients[base_account_broker][base_account_name].session
underlying_exchange = "NSE"
underlying = "NIFTY 50"
scrip = "NIFTY"
exchange = 'NFO'
strike_diff = 50
no_of_strikes = 10
lp = session.ltp(underlying_exchange + ':' + underlying)
lp = lp[underlying_exchange + ':' + underlying]['last_price']
atm = General.round_multiple(lp,strike_diff)
instrument_list = pd.read_csv("files\\instrument_list.csv")
instrument_list = instrument_list[instrument_list['name'] == scrip]
instrument_list['expiry'] = pd.to_datetime(instrument_list['expiry'])
current_expiry_date = instrument_list['expiry'].min().date()
instrument_list = instrument_list[instrument_list['name'] == scrip]

def instr_tokens():
    strikes = Trading.instr_list('self', session, underlying, 
                                 underlying_exchange, strike_diff, no_of_strikes)
    df = instrument_list[instrument_list['strike'].isin(strikes)].reset_index(drop=True)
    instrument_tokens = df['instrument_token']
    instrument_tokens.to_csv('files\\instrument_tokens.csv', index =False)
    return instrument_tokens

def underlying_token(session, underlying_exchange):
    inst = session.instruments(underlying_exchange)
    inst = pd.DataFrame(inst)
    token = inst['instrument_token'][inst['name'] == underlying].squeeze()
    return token
    
instrument_tokens = instr_tokens().squeeze().to_list()
underlying_token = underlying_token(session, underlying_exchange)
underlying_token = int(underlying_token)
instrument_tokens.append(underlying_token)


def option_type(op):
    if op == 'CE':
        return 'c'
    if op =='PE':
        return 'p'
    
def get_greeks(df):
    r = 10 #risk free rate
    t = Trading.days_to_expiry('self', current_expiry_date) + (1-Trading.day_fraction('self'))
    bsm = op.black_scholes(K=df.strike, St=df.spot_price, r=r, t=t, 
                           v=df.iv, type=df.op)
    return bsm

# Scheduling tasks
bs = BackgroundScheduler()
stoptime = time(15,15,5)
stoptime = dt.combine(date.today(), stoptime)

bs.add_job(Trading.get_iv, 'interval',id = 'nse_iv',
           minutes = 3, start_date= dt.today(), end_date=stoptime, 
           jitter = 2, replace_existing= True, args =('self',instrument_list, scrip),
           misfire_grace_time = 3)

'''ap.add_job(instr_list, 'cron', id = 'instru_list', day_of_week='mon-fri',
            hour=9, minute=24, args = (), replace_existing= True,
            misfire_grace_time = 3)

ap.add_job(squareoff, 'cron', id = 'squareoff_event', day_of_week='mon-fri',
            hour=15, minute=15, args = (clients,), replace_existing= True,
            misfire_grace_time = 3)'''
bs.start()

kws = KiteTicker(base_account.api_key,base_account.access_token)


##################################
def on_ticks(ws,ticks):
    # Callback to receive ticks.
    #logging.debug("Ticks: {}".format(ticks))
    #print(ticks['last_price'])
    global ticktick
    global tick
    global iv
    global df
    global df2
    tick = ticks
    #print(tick)
    df = pd.DataFrame(tick, columns= ['instrument_token','last_price', 'tradable']).set_index('instrument_token')
    #underlying_price = df[df['tradable'] == False]['last_price'].min()
    try: 
        iv = pd.read_csv('files\\impliedVolatility.csv')
        df2 = pd.merge(df.drop(columns=['tradable']), iv, left_on=['instrument_token'], 
                       right_on=['instrument_token'],
                       how = 'inner')
        df2['op'] = df2['instrument_type'].apply(option_type)
        df2['spot_price'] = df[df['tradable'] == False]['last_price'].min()
        #df2['risk_free_rate'] = 10
        #df2['time_to_expiry'] = Trading.days_to_expiry('self', current_expiry_date) + (1-Trading.day_fraction('self'))
        
        df2['val'], df2['val_int'],df2['delta'],df2['theta'],df2['rho'],df2['gamma'],df2['vega'] = df2.apply(get_greeks, axis=1).str
        df2 = df2.round(decimals=4).sort_values(['strike','instrument_type'], axis=0, ascending=[True,True]).reset_index(drop=True)
        print(df2[['strike','instrument_type','last_price', 'val', 'val_int', 'delta']])
    except:
        print(df)
    return

def on_connect(ws,response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    #logging.debug("on connect: {}".format(response))
    ws.subscribe(instrument_tokens)
    ws.set_mode(ws.MODE_LTP,instrument_tokens) # Set all token tick in `full` mode.
    #ws.set_mode(ws.MODE_FULL,[tokens[0]])  # Set one token tick in `full` mode.

def on_close(ws, code, reason):
    # On connection close stop the event loop.
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()
    

#def ticker():
kws.on_ticks=on_ticks
kws.on_connect=on_connect
kws.close = on_close
kws.connect()



    
    
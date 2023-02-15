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
from tradingclasses import Client, Trading
from generalclasses import General



"""-----------------------------------------------------------------------------"""
# Changing Current Working Directory
cwd = os.chdir("C:\\Users\\Yugenderan\\OneDrive\Professional Development\\Programming_Everything\\Trading")
"""-----------------------------------------------------------------------------"""

strategy = 'nap'
base_account = 'iampl'
client_data = pd.read_csv("files\\clients_list.csv", index_col='client_name')
client_data = client_data[client_data[strategy] > 0].fillna('a')
client_data = client_data.T
clients = {}
for name in client_data:
    clients[name] = Client(client_data[name], strategy)

session = Client.session('self', base_account ,clients)
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

def get_iv():
    ## Importing Options Chain From NSE
    # Urls for fetching Data
    url_oc      = "https://www.nseindia.com/option-chain"
    url_bnf     = 'https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY'
    url_nf      = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
    url_indices = "https://www.nseindia.com/api/allIndices"
    
    # Headers
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
                'accept-language': 'en,gu;q=0.9,hi;q=0.8',
                'accept-encoding': 'gzip, deflate, br'}
    
    sess = requests.Session()
    cookies = dict()
    
    # Local methods
    def set_cookie():
        request = sess.get(url_oc, headers=headers, timeout=5)
        cookies = dict(request.cookies)
    
    def get_data(url):
        set_cookie()
        response = sess.get(url, headers=headers, timeout=5, cookies=cookies)
        if(response.status_code==401):
            set_cookie()
            response = sess.get(url_nf, headers=headers, timeout=5, cookies=cookies)
        if(response.status_code==200):
            return response.text
        return ""
    
    response_text = get_data(url_nf)
    data = json.loads(response_text)
    
    # Fetching CE and PE data based on Nearest Expiry Date
    #currExpiryDate = data["records"]["expiryDates"][0]
    d2 = data["filtered"]["data"]
    CE = []
    PE = []
    for item in d2:
        for k,v in item.items():
            if k == 'CE':
                CE.append(v)
            elif k == 'PE':
                PE.append(v)
    ce_df = pd.DataFrame(CE)
    ce_df['instrument_type'] = 'CE'
    pe_df = pd.DataFrame(PE)
    pe_df['instrument_type'] = 'PE'
    left = instrument_list[['strike', 'instrument_token', 'instrument_type']]
    right1 = ce_df[['strikePrice', 'impliedVolatility','instrument_type']]
    right2 = pe_df[['strikePrice', 'impliedVolatility','instrument_type']]
    ce_iv = pd.merge(left, right1, left_on=['strike', 'instrument_type'], 
                  right_on=['strikePrice', 'instrument_type'])
    pe_iv = pd.merge(left, right2, left_on=['strike', 'instrument_type'], 
                  right_on=['strikePrice', 'instrument_type'])
    #ce__df = ce_df[['strikePrice', 'impliedVolatility']]
    iv = pd.concat([ce_iv, pe_iv],axis = 0, join = 'outer', ignore_index=True)
    iv = iv.sort_values('strike').reset_index(drop=True).drop(columns=['strikePrice'])
    iv = iv.rename(columns={'impliedVolatility':'iv'})
    return iv


kws = KiteTicker(clients[base_account].api_key,clients[base_account].access_token)

def on_ticks(ws,ticks):
    # Callback to receive ticks.
    #logging.debug("Ticks: {}".format(ticks))
    #print(ticks['last_price'])
    global ticktick
    global tick
    global iv
    global df
    tick = ticks
    #print(tick)
    df = pd.DataFrame(tick, columns= ['instrument_token','last_price', 'tradable']).set_index('instrument_token')
    underlying_price = df[df['tradable'] == False]['last_price'].min()
    iv = get_iv()
    df2 = pd.merge(df.drop(columns=['tradable']), iv, left_on=['instrument_token'], 
                   right_on=['instrument_token'],
                   how = 'inner')
    df2['op'] = df2['instrument_type'].apply(option_type)
    df2['spot_price'] = df[df['tradable'] == False]['last_price'].min()
    df2['bsm'] = df2['spot_price'].apply(get_greeks, args=(df2['strike'], df2['op'], df2['iv']))
    print(df2)
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
#kws.close()






#iv = get_iv()

#calcuting current time in terms of fraction of trading hours
'''today = date.today()
opentime = time(9,15)
openingtime = dt.combine(today, opentime)
trading_seconds = 22500

'''
'''
#Declare parameters
K=17500    #strike price
St=17763.45   #current stock price
r=10      #4% risk free rate
t=4 - ratio    #time to expiry, 30 days 
v=15.35    #volatility 
types='c' #Option type call
#Black Scholes Model
bsm=op.black_scholes(K=K, St=St, r=r, t=t, 
                     v=v, type=types)
print(str(K), str(types))
for k,v in bsm['greeks'].items():
    print(str(k) +' : '+ str(v))
for k,v in bsm['value'].items():
    print(str(k) +' : '+ str(v))'''
''''''
def get_greeks(underlying_price, strike, option_type, iv):
    r = 10 #risk free rate
    t = Trading.days_to_expiry('self', current_expiry_date) + (1-Trading.day_fraction('self'))
    bsm = op.black_scholes(K=strike, St=underlying_price, r=r, t=t, 
                           v=iv, type=option_type)
    return bsm
    
def option_type(op):
    if op == 'CE':
        return 'c'
    if op =='PE':
        return 'p'
        

    
    
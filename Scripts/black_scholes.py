# Libraries
import opstrat as op
import pandas as pd
import requests
import json
import math
from kiteconnect import KiteConnect, KiteTicker
from datetime import date
from datetime import timedelta
from datetime import datetime as dt
from datetime import time
from tradingclasses import Client, Trading
from generalclasses import General

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
instrument_list = instrument_list[instrument_list['name'] == scrip]

def instr_tokens():
    strikes = Trading.instr_list('self', session, underlying, 
                                 underlying_exchange, strike_diff, no_of_strikes)
    
    df = instrument_list[instrument_list['strike'].isin(strikes)].reset_index(drop=True)
    instrument_tokens = df['instrument_token']
    instrument_tokens.to_csv('files\\instrument_tokens.csv', index =False)
    
instrument_tokens = pd.read_csv('files\\instrument_tokens.csv')
instrument_tokens_list = instrument_tokens.squeeze().to_list()

kws = KiteTicker(clients[base_account].api_key,clients[base_account].access_token)

def on_ticks(ws,ticks):
    # Callback to receive ticks.
    #logging.debug("Ticks: {}".format(ticks))
    #print(ticks['last_price'])
    global ticktick
    global tick
    global df
    tick = ticks
    df = pd.DataFrame(tick, columns= ['instrument_token','last_price']).set_index('instrument_token')
    
    for op_type in symbols_list:
        for symb in df.T:
            if symbols_list[op_type].instrument_token == symb:
                symbols_list[op_type].last_price = df['last_price'][symb]
                
    sym = pd.DataFrame()
    write_check = False
    for item in symbols_list:
        try:
            if symbols_list[item].last_price >= symbols_list[item].trigger_price:
                symbols_list[item].position_open = 0
            else:
                pass
        except Exception as e:
            logging.info("{}".format(e))
                
        if symbols_list[item].position_open == 1:
            poss = True
            print('symbol: ' + item +'| '+ str(symbols_list[item].strike)+'| ltp: '+ str(symbols_list[item].last_price) +'| target: '+ str(symbols_list[item].target)+'| sl: '+ str(symbols_list[item].trigger_price)+'| pos_open : ' + str(poss))
        elif symbols_list[item].position_open == 0:
            poss = False
        ##    

        if symbols_list[item].last_price <= symbols_list[item].target and poss == True:
            write_check = True
            symbols_list[item].trigger_price = round(symbols_list[item].target + symbols_list[item].initial_stoploss,2)
            symbols_list[item].stoploss =General.round_multiple(symbols_list[item].trigger_price * 1.05,0.05)
            symbols_list[item].target = round(symbols_list[item].target - symbols_list[item].initial_target,2)
            
            for username in clients:
                kite = General.generate_trading_session(username,clients)
                order = kite.orders()
                order = pd.DataFrame(order)
                order = order[order["product"] == product]
                order = order[order['tradingsymbol'] == symbols_list[item].tradingsymbol]
                order = order[order['status'] == "TRIGGER PENDING"]
                order = order.squeeze()
                order_id = int(order['order_id'])
                
                try:
                    kite.modify_order(variety=kite.VARIETY_REGULAR, order_id = order_id,
                                                  price= symbols_list[item].stoploss,
                                                  trigger_price= symbols_list[item].trigger_price)
                    print("stoploss order modified for " + username + ' for ' + item)

                except Exception as e:
                    logging.info("Error placing SL order: {}".format(e))
        
        ddd = pd.Series(vars(symbols_list[item]))
        sym = sym.append(ddd, ignore_index= True)
    if write_check == True:
        sym.to_csv(file + 'ap_live.csv', index = False, encoding=None)

    #print(ticks)
    if datetime.now() > stoptime:
        ws.stop()
        ap.shutdown(wait = False)
    return


def on_connect(ws,response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    #logging.debug("on connect: {}".format(response))
    ws.subscribe(instrument_tokens_list)
    ws.set_mode(ws.MODE_LTP,instrument_tokens_list) # Set all token tick in `full` mode.
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
currExpiryDate = data["records"]["expiryDates"][0]
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
pe_df = pd.DataFrame(PE)

ce__df = ce_df[['strikePrice', 'impliedVolatility']]
iv = pd.merge(ce_df[['strikePrice', 'impliedVolatility']],
              pe_df[['strikePrice', 'impliedVolatility']],
              left_on=['strikePrice'],right_on=['strikePrice'], how='inner')
iv.rename(columns = {'impliedVolatility_x':'ce_iv','impliedVolatility_y':'pe_iv'}, inplace = True)

#calcuting current time in terms of fraction of trading hours
today = date.today()
opentime = time(9,15)
openingtime = dt.combine(today, opentime)
current_time = dt.now()
trading_seconds = 22500
diff = (current_time - openingtime)
diff2 = diff.total_seconds()
ratio = diff2/trading_seconds
if ratio > 1:
    ratio = 1
    
#Declare parameters
K=17500    #spot price
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
    print(str(k) +' : '+ str(v))



# Libraries
import opstrat as op
import pandas as pd
import requests
import json
import math

from kiteconnect import KiteConnect
from datetime import date
from datetime import timedelta
from datetime import datetime as dt
from datetime import time
from mytradingclasses import General, Client



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
underlying_exchange = "NSE"
underlying = "NIFTY 50"
kite = 
lp = kite.ltp(underlying_exchange + ':' + underlying)
lp = lp[underlying_exchange + ':' + underlying]['last_price']
atm = General.round_multiple(lp,strike_diff)

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



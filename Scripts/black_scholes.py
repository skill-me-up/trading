import opstrat as op
import pandas as pd


from datetime import date
from datetime import timedelta
from datetime import datetime as dt
from datetime import time




#calcuting current time in terms of fraction of trading hours
today = date.today()
opentime = time(0,0)
openingtime = dt.combine(today, opentime)
current_time = dt.now()
trading_seconds = 22500
diff = (current_time - openingtime)
diff2 = diff.total_seconds()
ratio = diff2/trading_seconds


#ts = 86400
#diff3 = (current_time - openingtime)
#ratio = diff3.total_seconds()/ts
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



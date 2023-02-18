# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 11:22:49 2023

@author: Yugenderan
"""

"""
This contains iron condor strategy execution codes for multiple accounts 
with multiple brokers as intermediaries
"""

# importing required modules
import os
import logging
import datetime as dt
import time
from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
from kiteconnect import KiteConnect
from dhanhq import dhanhq
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from tradingclasses import Client, Trading
from generalclasses import General

logging.basicConfig(level=logging.INFO)


###############################################################################
# Changing Current Working Directory
cwd = os.chdir("C:\\Users\\Yugenderan\\OneDrive\Professional Development\\Programming_Everything\\Trading")
###############################################################################
#inputs
today = date.today()
strategy = 'ironcondor'
underlying = 'NIFTY BANK'
underlying_exchange = 'NSE'
scrip = 'BANKNIFTY'
scrip_exchange = 'NFO'

#Importing Clients data from clients_list file
client_data = pd.read_csv("files\\clients_list.csv", index_col='client_name')
client_data['validity'] = pd.to_datetime(client_data['validity']).dt.date
client_data = client_data[client_data[strategy] > 0].fillna('a')
brokers = client_data['broker'].tolist()

#converting clients data into clients class objects
#client_data = client_data.T
clients = {}
for broker in brokers:
    clients[broker] = {}
    cl_data = client_data[client_data['broker'] == broker].T
    for name in cl_data:
        clients[broker][name] = Client(cl_data[name], strategy)
        
#importing base account for current strategy
base_ac = pd.read_csv("files\\base_accounts.csv", index_col='strategy').squeeze()
base_ac = base_ac.loc[strategy]

#importing instruments list for current expiry
instrument_master = pd.read_csv("files\\instrument_list.csv")
instrument_master['expiry'] = pd.to_datetime(instrument_master['expiry']).dt.date
instruments = instrument_master[instrument_master['name'] == scrip]

#retriving current expiry date from instrument list
expiry = instruments['expiry'].min()
current_expiry_date = expiry

#get days to expiry
try:
    days_to_expiry = Trading.days_to_expiry_bd('self', expiry)
except:
    days_to_expiry = Trading.days_to_expiry_ad('self', expiry)

#importing working days to findout entry date        
working_days = pd.read_excel('files\\working_days.xlsx').squeeze().dt.date.to_list()
entry_date = working_days[working_days.index(expiry) - 3]

#creating session for base account
kite_session = clients[base_ac].session



#adding times to entry and exit dates
entry_time = dt.time(10,0,0)
exit_time = dt.time(15,15,0)

#combining date and time to use scheduling function
entry_date = datetime.combine(entry_date, entry_time)
exit_date = datetime.combine(expiry, exit_time)

time_gap =15
legs = 5


def entry(clients, instruments,legs, base_ac, expiry):
    """Entry into the ironcondor position"""
    global symbols
    symbols= Trading.strangle_selection('self',clients['zerodha'][base_ac].session, 
                                        underlying,instruments,
                                        1000,100,True,1500,'short')
    symbols.to_csv("files\\ironcondor\\"+str(expiry)+'.csv',
                 index = False, encoding=None)
    
    lot_size =symbols.lot_size[0]
    #Expiry Day condition Checking and placing orders
    if today == entry_date:
        for broker in clients:
            if broker == 'zerodha':
                symbols = symbols.sort_values(['instrument_type','buy/sell'], ascending=False,).reset_index(drop=True)
                for username in clients[broker]:
                    print('Placing orders for '+username)
                    total_quantity = Trading.position_size_margin('self', 100000,
                                                            clients[broker][username],
                                                            lot_size)
                    max_quantity = 150
                    remaining_quantity = total_quantity
                    while remaining_quantity != 0:
                        order_quantity, remaining_quantity = Trading.orderslicing('self', total_quantity, max_quantity, remaining_quantity)
                        for num in symbols.index:
                            symbol = symbols.loc[num]
                            order = Trading.place_order(tag = strategy,
                                                        client=clients[broker][username],
                                                        symbol=symbol,
                                                        quantity=order_quantity,
                                                        order_type='market',
                                                        product='NRML')
                        
                        time.sleep(0.5)
                    print('Full order placed for '+username)
            elif broker == 'dhan':
                symbols = symbols.sort_values(['instrument_type','buy/sell'], ascending=True,).reset_index(drop=True)
                for username in clients[broker]:
                    print('Placing orders for '+username)
                    total_quantity = Trading.position_size_margin('self', 100000,
                                                            clients[broker][username],
                                                            lot_size)
                    max_quantity = 300
                    remaining_quantity = total_quantity
                    while remaining_quantity != 0:
                        order_quantity, remaining_quantity = Trading.orderslicing('self', total_quantity, max_quantity, remaining_quantity)
                        for num in symbols.index:
                            symbol = symbols.loc[num]
                            order = Trading.place_order(tag=strategy,
                                                        client=clients[broker][username], 
                                                        symbol=symbol,
                                                        quantity=order_quantity,
                                                        order_type ='market', 
                                                        product ='NRML',)
                        time.sleep(0.5)
                    print('Full order placed for '+username)
                    
    return

            
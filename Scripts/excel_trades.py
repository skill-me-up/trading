# -*- coding: utf-8 -*-
"""
Created on Mon Feb 20 15:10:41 2023

@author: Yugenderan
"""

"""Program to run take trades from Excel"""
#importing Modules
import os
import pandas as pd
import numpy as np
from tradingclasses import Client, Trading

"""-----------------------------------------------------------------------------"""
# Changing Current Working Directory
cwd = os.chdir("C:\\Users\\Yugenderan\\OneDrive\Professional Development\\Programming_Everything\\Trading")
"""-----------------------------------------------------------------------------"""
#importing client data
client_data = pd.read_csv("files\\clients_list.csv", index_col='client_name')
client_data['validity'] = pd.to_datetime(client_data['validity'],
                                         format="%d-%m-%Y", ).dt.date
no_of_clients =len(client_data)
#getting list of brokers from clients data
brokers = client_data['broker'].tolist()

#importing trade data
trade_data = pd.read_excel('front_end.xlsx',sheet_name='fresh_orders',
                           engine='openpyxl').T
trade_accounts = trade_data[-no_of_clients:]
trade_data = trade_data[:-no_of_clients]

#importing instruments list
instrument_master = pd.read_csv("files\\instrument_list.csv")
instrument_master['expiry'] = pd.to_datetime(instrument_master['expiry']).dt.date


clients = {}
for broker in brokers:
    clients[broker] = {}
    cl_data = client_data[client_data['broker'] == broker].T
    for name in cl_data:
        clients[broker][name] = Client(cl_data[name])



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
from datetime import date
from datetime import datetime
from datetime import timedelta
from kiteconnect import KiteConnect
from dhanhq import dhanhq
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from tradingclasses import Client

logging.basicConfig(level=logging.INFO)


###############################################################################
# Changing Current Working Directory
cwd = os.chdir("C:\\Users\\Yugenderan\\OneDrive\Professional Development\\Programming_Everything\\Trading")
###############################################################################
strategy = 'ironcondor'
client_data = pd.read_csv("files\\clients_list.csv", index_col='client_name')
client_data = client_data[client_data[strategy] > 0].fillna('a')
client_data = client_data.T
clients = {}
for name in client_data:
    clients[name] = Client(client_data[name], 'nap')


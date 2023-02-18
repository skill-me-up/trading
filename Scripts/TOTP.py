# -*- coding: utf-8 -*-
"""
Created on Mon Aug  8 10:44:30 2022

@author: Yugenderan
"""

# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
from pyotp import TOTP
import os
import sys
sys.path.append(r'D:\Zerodha API TEST\1_account_authorization\Scripts')
from myclasses import Client, General

cwd = os.chdir("D:\\Zerodha API TEST\\1_account_authorization")


client_data = pd.read_excel("clients_list.xlsx",sheet_name= "live_accounts",
                            index_col=("client_name"))

client_data = client_data[client_data["live"] == "Yes"]
client_data['capital'] = client_data['capital'].replace('Rs.',"", regex = True)
#Retriving base account for the strategy
base_account = client_data[client_data['base_account'] == "Yes"].index
base_account = base_account[0]

#transponding the client data to make it feasible for client object generation
client_data = client_data.T

#importing access-tokens generated from pre-market program
access_token = pd.read_excel("access_tokens.xlsx", sheet_name= "tokens", 
                             index_col=("client_name")).T

###############################################################################      
   
# Creating instances of clients class with clients data
clients = {}
for name in client_data:
    clients[name] = Client(client_data[name], access_token[name])  

for k in clients.keys():
    #print(clients[k].authenticator_id)
    totp = TOTP(clients[k].authenticator_id)
    token = totp.now()
    print(k+ ":" +str(token))
    
    
#kite = General.generate_trading_session('ranjith', clients)
#pos = kite.positions()

# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 10:24:31 2022

@author: Yugenderan
"""

"""
Files List:
    clients_list.xlsx
"""
'''import requests   
url = "https://images.dhan.co/api-data/api-scrip-master.csv"
req = requests.get(url)
url_content =req.content
csv_file = open("dhan_api-scrip_master.csv", "wb")
csv_file.write(url_content)
csv_file.close()'''
#!/usr/bin/env algo

from kiteconnect import KiteConnect
from selenium import webdriver
import time
import os
from pyotp import TOTP
from datetime import date
import pandas as pd
from tradingclasses import Client

"""-----------------------------------------------------------------------------"""
# Changing Current Working Directory
cwd = os.chdir("C:\\Users\\Yugenderan\\OneDrive\Professional Development\\Programming_Everything\\Trading")
"""-----------------------------------------------------------------------------"""

def autologin(user, client_data):
    kite = KiteConnect(api_key=client_data.loc[user, "API_key"])
    service = webdriver.chrome.service.Service('./chromedriver')
    service.start()
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    driver = webdriver.Remote(service.service_url,options=options)
    driver.get(kite.login_url())
    driver.implicitly_wait(5)
    username = driver.find_element("xpath",'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input')
    password = driver.find_element("xpath",'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
    username.send_keys(client_data.loc[user, "broker_id"])
    password.send_keys(client_data.loc[user, "password"])
    
    driver.find_element("xpath",'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[4]/button').click()
    time.sleep(5)
    totp_text_field = driver.find_element("xpath",'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
                                                                                                                        
    totp = TOTP(client_data.loc[user, "authenticator_id"])
    token = totp.now()
    totp_text_field.send_keys(token)
   
    driver.find_element("xpath", '/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[3]/button').click()
    time.sleep(5)
    request_token=driver.current_url.split('request_token=')[1][:32]
    driver.quit()

    #generating access token - valid till 6 am the next day
    data = kite.generate_session(request_token, api_secret=client_data.loc[user, "API_secret"])
    return data

"""-----------------------------------------------------------------------------"""

def multi_autologin():
    ##Getting List of Clients to trade today
    client_data = pd.read_csv("files\\clients_list.csv", index_col='client_name')
    client_data['validity'] = pd.to_datetime(client_data['validity'], format="%d-%m-%Y").dt.date
    strategies_list = client_data.columns[-6:].to_list()
    client_data['live'] = client_data[strategies_list].sum(axis=1) > 0
    
    #getting list of zerodha accounts that needs access tokens
    cl_d = client_data[client_data['broker'] == "zerodha"]
    cl_d = cl_d[cl_d["live"] == True]
    
    #Generating access tokens for live accounts
    for username in cl_d.index:
        print('Logging in '+ username)
        data = autologin(username, client_data)
        client_data.loc[username, "access_token"] = data["access_token"]        
        client_data.loc[username, 'validity'] = date.today()
    # dropping live column from master clients list.
    client_data = client_data.drop(['live'], axis = 1)
    # writing client data back into csv file with obtained access token
    client_data.to_csv("files\\clients_list.csv", index = True)
    print('Access tokens generated for live accounts')
    return client_data

"""-----------------------------------------------------------------------------"""
def instrument_dump(kite):
    global instrument_list
    global instrument_list_next
    instrument_dump = kite.instruments("NFO")
    instrument_df = pd.DataFrame(instrument_dump)
    
    instr_names = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
    instrument_list = pd.DataFrame()
    instrument_list_next = pd.DataFrame()
    for name in instr_names:
        data = instrument_df[instrument_df["name"] == name]
        expiry = data["expiry"].drop_duplicates()
        expiry = expiry.sort_values().reset_index(drop=True)
        current_expiry = expiry[0]
        next_expiry = expiry[1]
        data1 = data[data['expiry'] == current_expiry]
        data2 = data[data['expiry'] == next_expiry]
        instrument_list = pd.concat([instrument_list,data1],axis = 0,
                                    join ='outer', ignore_index=True)
                                    
        instrument_list_next = pd.concat([instrument_list_next,data2],
                                         axis = 0,join ='outer', 
                                         ignore_index=True)    
    instrument_list.to_csv("files\\instrument_list.csv", index = False)
    print("instruments list generated for current expiry")
    instrument_list_next.to_csv("files\\instrument_list_next.csv", index = False)
    print("instruments list generated for next expiry")
    return 
"""-----------------------------------------------------------------------------"""
#Function for Pre-market requirements
def pre_market():
    client_data = multi_autologin()
    client_data = client_data.T
    clients = {}
    for name in client_data:
        clients[name] = Client(client_data[name]) 
    instrument_dump(clients['iampl'].session)


pre_market()

#premarket_sched = BackgroundScheduler()

#premarket_sched.add_job(pre_market, 'cron', id = 'pre-market_login', day_of_week='mon-fri',
#            hour=9, minute=15, replace_existing= True,
#            misfire_grace_time = 3)


#premarket_sched.start()

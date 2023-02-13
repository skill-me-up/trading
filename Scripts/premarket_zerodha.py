# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 10:24:31 2022

@author: Yugenderan
"""

"""
Files List:
    index list.txt
    clients_list.xlsx
    access_tokens.xlsx
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
#import logging
import datetime as dt
from datetime import date
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import openpyxl

"""-----------------------------------------------------------------------------"""
# Changing Current Working Directory
cwd = os.chdir("C:\\Users\\Yugenderan\\OneDrive\Professional Development\\Programming_Everything\\Trading")


"""-----------------------------------------------------------------------------"""

def autologin(user, client_data):
    kite = KiteConnect(api_key=client_data["API_key"][user])
    service = webdriver.chrome.service.Service('./chromedriver')
    service.start()
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options = options.to_capabilities()
    driver = webdriver.Remote(service.service_url, options)
    driver.get(kite.login_url())
    driver.implicitly_wait(5)
    username = driver.find_element("xpath",'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input')
    password = driver.find_element("xpath",'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
    username.send_keys(client_data["broker_id"][user])
    password.send_keys(client_data["password"][user])
    
    driver.find_element("xpath",'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[4]/button').click()
    time.sleep(5)
    totp_text_field = driver.find_element("xpath",'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
                                                                                                                        
    totp = TOTP(client_data["authenticator_id"][user])
    token = totp.now()
    totp_text_field.send_keys(token)
   
    driver.find_element("xpath", '/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[3]/button').click()
    time.sleep(5)
    request_token=driver.current_url.split('request_token=')[1][:32]
    driver.quit()

    #generating access token - valid till 6 am the next day
    data = kite.generate_session(request_token, api_secret=client_data["API_secret"][user])
    return data

"""-----------------------------------------------------------------------------"""

def multi_autologin():
    ##Getting List of Clients to trade today
    global client_data
    global access_token
    global base_account
    
    client_data2 = pd.read_csv("files\\clients_list.csv", index_col='client_name')
    cl_d = client_data2[client_data2['broker'] == "zerodha"]
    #client_data = pd.read_excel("clients_list.xlsx",sheet_name= "live_accounts", index_col=("client_name"))
    cl_d = cl_d[cl_d["live"] == "Yes"]
    base_account = client_data[client_data['base_account'] == "Yes"].index
    base_account = base_account[0]
    ##Getting Access token for all Clients
    access_token = pd.read_excel("access_tokens.xlsx", sheet_name= "tokens", index_col=("client_name"))
    
    for username in client_data.index:
        data = autologin(username, client_data)
        access_token["access_token"][username] = data["access_token"]
        access_token["token_time"][username] = dt.datetime.now()
    
    #storing Access token in excel file
    access_token = access_token.dropna()  
    access_token.to_excel("access_tokens.xlsx", sheet_name= "tokens", index = True, engine= "openpyxl", encoding=None)
    print('Access tokens generated for live accounts')
    return access_token

"""-----------------------------------------------------------------------------"""

### Function to Generate trading Session
def generate_trading_session(client_data,user,access_token):    
    kite = KiteConnect(api_key=client_data["API_key"][user])
    kite.set_access_token(access_token["access_token"][user])
    print("Session created for " + user)
    return kite

"""-----------------------------------------------------------------------------"""
def instrument_dump(kite):
    global instrument_list
    instrument_dump = kite.instruments("NFO")
    instrument_df = pd.DataFrame(instrument_dump)
    data = instrument_df[instrument_df["name"] == "NIFTY"]
    data = data.append(instrument_df[instrument_df["name"] == "BANKNIFTY"])
    finnifty = instrument_df[instrument_df["name"] == "FINNIFTY"]
    #getting list of expiries
    all_expiry = data["expiry"].drop_duplicates()
    all_expiry = all_expiry.sort_values().reset_index(drop=True)
    current_expiry = all_expiry[0]
    next_expiry = all_expiry[1]
    #filtering instruments based on current expiry
    instrument_list = data[data["expiry"] == current_expiry]
    instrument_list.to_excel("instrument_list.xlsx", sheet_name= "instruments", index = False, engine= "openpyxl", encoding=None)
    #filtering instruments based on next expiry
    instrument_list_next = data[data["expiry"] == next_expiry]
    instrument_list_next.to_excel("instrument_list_next.xlsx", sheet_name= "instruments", index = False, engine= "openpyxl", encoding=None)
    print("instruments list generated for NF & BNF " + str(current_expiry) + " expiry")
    print("instruments list generated for NF & BNF " + str(next_expiry) + " expiry")
    fin_all_expiry = finnifty["expiry"].drop_duplicates()
    fin_all_expiry = fin_all_expiry.sort_values().reset_index(drop=True)
    fin_current_expiry = fin_all_expiry[0]
    fin_next_expiry = fin_all_expiry[1]
    #filtering instruments based on current expiry
    fin_instrument_list = finnifty[finnifty["expiry"] == fin_current_expiry]
    fin_instrument_list.to_excel("finnifty_instrument_list.xlsx", sheet_name= "instruments", index = False, engine= "openpyxl", encoding=None)
    #filtering instruments based on next expiry
    fin_instrument_list_next = finnifty[finnifty["expiry"] == fin_next_expiry]
    fin_instrument_list_next.to_excel("finnifty_instrument_list_next.xlsx", sheet_name= "instruments", index = False, engine= "openpyxl", encoding=None)
    print("instruments list generated for finnifty " + str(fin_current_expiry) + " expiry")
    print("instruments list generated for finnifty " + str(fin_next_expiry) + " expiry")
    return instrument_list

"""-----------------------------------------------------------------------------"""
#Function for Pre-market requirements
def pre_market():
    multi_autologin()
    kite = generate_trading_session(client_data, base_account, access_token)
    instrument_dump(kite)


pre_market()

#kite = generate_trading_session(client_data, user, access_token)
#premarket_sched = BackgroundScheduler()

#premarket_sched.add_job(pre_market, 'cron', id = 'pre-market_login', day_of_week='mon-fri',
#            hour=9, minute=15, replace_existing= True,
#            misfire_grace_time = 3)


#premarket_sched.start()

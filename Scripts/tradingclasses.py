# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 10:56:42 2023

@author: Yugenderan
"""

from kiteconnect import KiteConnect
from dhanhq import dhanhq
from generalclasses import General
from datetime import datetime as dt, date, time
import pandas as pd
import requests
import json


class Client:
    '''helps to create objects of clients data'''
    def __init__(self, client_data,strategy):
        '''intialize data'''
        self.name = client_data.name
        self.broker = client_data['broker']
        self.broker_id = client_data['broker_id']
        self.api_key = client_data['API_key']
        self.api_secret = client_data['API_secret']
        self.password = client_data['password']
        self.authenticator_id = client_data['authenticator_id']
        self.access_token = client_data['access_token']
        self.validity = client_data['validity']
        self.capital = client_data[strategy]
        #Create New trading Session
        if self.broker == 'zerodha':
            session = KiteConnect(api_key=self.api_key)
            session.set_access_token(self.access_token)
        
        elif self.broker == 'dhan':
            session = dhanhq(self.broker_id, self.access_token)
        
        self.session = session
        
###############################################################################       
class Trading:
    '''contains all methods needed for trading'''
    def session(self, user, clients):
        '''Create New trading Session'''
        if clients[user].broker == 'zerodha':
            session = KiteConnect(api_key=clients[user].api_key)
            session.set_access_token(clients[user].access_token)
        
        elif clients[user].broker == 'dhan':
            session = dhanhq(clients[user].broker_id, clients[user].access_token)
        
        return session
    
    def instr_list(self, session, underlying, exchange, strike_diff, no_of_strikes):
        '''use only zerodha session for this method'''
        lp = session.ltp(exchange + ':' + underlying)
        lp = lp[exchange + ':' + underlying]['last_price']
        atm = General.round_multiple(lp,strike_diff)
        strikes = []
        for num in range(no_of_strikes):
            strikes.append(atm+(num*strike_diff))
            strikes.append(atm-(num*strike_diff))
        strikes = list(set(strikes))
        strikes.sort()
        return strikes

    def days_to_expiry(self, current_expiry_date):
        today = date.today()
        working_days = pd.read_excel('files\\working_days.xlsx')
        working_days["working_days"] = working_days['working_days'].dt.date
        expiry_index = working_days[working_days['working_days'] == current_expiry_date].index.values
        expiry_index = expiry_index[0]
        today_index = working_days[working_days['working_days'] == today].index.values
        today_index = today_index[0]
        days_to_expiry = expiry_index - today_index
        return days_to_expiry
    
    def day_fraction(self, close_time = time(15,30), open_time = time(9,15)):
        today = date.today()
        openingtime = dt.combine(today, open_time)
        closingtime = dt.combine(today, close_time)
        diff = (closingtime - openingtime).total_seconds()
        current_time = dt.today()
        frac = (current_time - openingtime).total_seconds()
        ratio = frac/diff
        if ratio > 1:
            ratio = 1
        return ratio
    
    def get_iv(self, instrument_list, scrip):
        ## Importing Options Chain From NSE
        # Urls for fetching Data
        url_oc      = "https://www.nseindia.com/option-chain"
        url_bnf     = 'https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY'
        url_nf      = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
        url_indices = "https://www.nseindia.com/api/allIndices"
        if scrip =='NIFTY':
            url = url_nf
        elif scrip == 'BANKNIFTY':
            url = url_bnf
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
        response_text = get_data(url)
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
        iv.to_csv('files\\impliedVolatility.csv', index =False)
        return iv
        
        
        def strangle_selection(kite_session, instrument_list, strike_diff, exchange, scrip):
            '''Strike selection based on given strike difference from atm'''
            #getting last traded price from kiteconnect
            exchange = 'NSE'
            scrip = 'NIFTY BANK'
            ltp = kite_session.ltp(exchange +':'+scrip)
            #converting data received to pandas dataframe
            data = {}
            data = pd.DataFrame(data, index=["spot_last_price"])
            for num in range(0,4):
                data[num]= ltp["NSE:NIFTY BANK"]["last_price"]
           
            data = data.T
            data["name"] = "BANKNIFTY"
            data["instrument_type"] = ["CE", "CE", "PE", "PE"]
            data["strike_difference"] = [1500,1000,-1000,-1500]
            #data = data[["name","spot_last_price"]]
           
            #finding atm and strike
            data["atm"] = round_multiple(data["spot_last_price"],100)
            data["strike"] = data["atm"] + data["strike_difference"]
           
           
            #getting symbol for selected strike prices
            symbols = pd.merge(data,instrument_list,left_on = ["name","instrument_type","strike"],
                                right_on=["name","instrument_type","strike"], how ="inner",)
            symbols = symbols.drop("last_price",axis = 1)
            return symbols
            
        
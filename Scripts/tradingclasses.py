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
        self.capital = client_data[strategy]
    
    def session(self, user, clients):
        '''Create New Kite Session'''
        if clients[user].broker == 'zerodha':
            session = KiteConnect(api_key=clients[user].api_key)
            session.set_access_token(clients[user].access_token)
        
        elif clients[user].broker == 'dhan':
            session = dhanhq(clients[user].broker_id, clients[user].access_token)
        
        return session

###############################################################################       
class Trading:
    '''contains all methods needed for trading'''
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
        
        
        
        
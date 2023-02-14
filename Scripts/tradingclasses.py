# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 10:56:42 2023

@author: Yugenderan
"""

from kiteconnect import KiteConnect
from dhanhq import dhanhq
from generalclasses import General


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

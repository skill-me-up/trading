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
import logging


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

    def days_to_expiry_bd(self, current_expiry_date):
        '''days to expiry in business days concept'''
        today = date.today()
        working_days = pd.read_excel('files\\working_days.xlsx')
        working_days["working_days"] = working_days['working_days'].dt.date
        expiry_index = working_days[working_days['working_days'] == current_expiry_date].index.values
        expiry_index = expiry_index[0]
        today_index = working_days[working_days['working_days'] == today].index.values
        today_index = today_index[0]
        days_to_expiry = expiry_index - today_index
        return days_to_expiry
    
    def days_to_expiry_ad(self, current_expiry_date):
        '''days to expiry in all days concept excluding today'''
        today = date.today()
        diff = (current_expiry_date - today).days
        return diff
    
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
        
        
    def strangle_selection(self,kite_session, underlying, instrument_list,
                           strike_dist, strike_diff = 100, 
                           hedge = False, hedge_dist = 0,
                           position = 'short'):
        '''Strike selection based on given strike difference from atm'''
        #getting last traded price from kiteconnect
        exchange = 'NSE'
        ltp = kite_session.ltp(exchange +':'+underlying)
        ltp = ltp[exchange + ':' + underlying]['last_price']
        atm = General.round_multiple(ltp,strike_diff)
        strangle = pd.DataFrame()
        strangle_dic = [('CE', 'sell'), ('PE', 'sell')]
        hedge_dic = [('CE', 'buy'), ('PE', 'buy')]

        for k,v in strangle_dic:
            if k == 'CE':
                a = pd.DataFrame([atm+strike_dist,k,v]).T
            elif k == 'PE':
                a = pd.DataFrame([atm-strike_dist,k,v]).T
            strangle = pd.concat([strangle,a])

        if hedge == True:
            for k,v in hedge_dic:
                if k == 'CE':
                    a = pd.DataFrame([atm+hedge_dist,k,v]).T
                elif k == 'PE':
                    a = pd.DataFrame([atm-hedge_dist,k,v]).T
                strangle = pd.concat([strangle,a])

        strangle =strangle.set_axis(('strike', 'instrument_type', 'buy/sell'), axis=1).reset_index(drop=True)
        if position =="long":
            strangle['buy/sell'] = strangle['buy/sell'].map({'buy':'sell', 'sell':'buy'})
        
        #getting symbol for selected strike prices
        symbols = pd.merge(instrument_list,strangle, left_on = ["instrument_type","strike"],
                            right_on=["instrument_type","strike"], how ="inner",)
        symbols = symbols.drop("last_price",axis = 1)
        return symbols
    
    def position_size_value(self, price, risk_value, lot_size=1):
        ''' Calculates Position size for the capital'''
        quantity = risk_value / price
        quantity = lot_size * round(quantity/lot_size)
        return quantity

    def position_size_margin(self, margin, clients, lot_size=1):
        lots = clients.capital/margin
        quantity = lots * lot_size
        return int(quantity)
    
    def orderslicing(self, total_quantity, max_quantity, remaining_quantity):
        '''Defines order quanitity after order slicing'''
        if remaining_quantity != 0:
            if remaining_quantity > max_quantity:
                order_quantity = max_quantity
                print("quantity is: " + str(order_quantity))
                remaining_quantity -= order_quantity

            else:
                order_quantity = remaining_quantity
                print("quantity is: " + str(order_quantity))
                remaining_quantity -= order_quantity

            #self.quantity = order_quantity
            #self.remaining_quantity = remaining_quantity

        return (order_quantity, remaining_quantity)
    
    
    def place_order(tag, client, symbol, quantity, order_type, product,
                    price = None, trigger_price = None,
                    buy_sell = None, exchange='NFO'):
        #client =clients['moshin']
        session = client.session
        try:
            buy_sell = symbol['buy/sell']
        except:
            pass
        
        try:
            exchange = symbol['exchange']
        except:
            pass
        
        if client.broker == 'zerodha':
            #symbol = "NIFTY22N1718700PE"
            #multiplier = 3
            #place Market Order for Options Market
            if buy_sell == "buy":
                t_type=session.TRANSACTION_TYPE_BUY
            elif buy_sell == "sell":
                t_type=session.TRANSACTION_TYPE_SELL
            
            if product == "MIS":
                product_type=session.PRODUCT_MIS
            elif product == "NRML":
                product_type=session.PRODUCT_NRML
                
            if order_type == "market":
                o_type=session.ORDER_TYPE_MARKET
            elif order_type == "limit":
                o_type=session.ORDER_TYPE_LIMIT
            elif order_type == "stoploss":
                o_type=session.ORDER_TYPE_SL
            
            if exchange == "NSE":
                exchange = session.EXCHANGE_NSE
            elif exchange == "NFO":
                exchange = session.EXCHANGE_NFO
            elif exchange == "BSE":
                exchange = session.EXCHANGE_BSE
            elif exchange == "BFO":
                exchange = session.EXCHANGE_BFO
                
            try:
                order = session.place_order(tag=tag,
                                            tradingsymbol=symbol.tradingsymbol,
                                            exchange=exchange,
                                            transaction_type=t_type,
                                            quantity=quantity,
                                            order_type=o_type,
                                            product=product_type,
                                            variety=session.VARIETY_REGULAR,
                                            trigger_price=trigger_price,
                                            price=price)
                                         
    
                logging.info("Order id: {}".format(order))
    
                print("order id : " + order)
    
            except Exception as e:
                logging.info("Error placing order: {}".format(e))
    
            return order
        
        elif client.broker== 'dhan':
            if price == None:
                price = 0
            if trigger_price== None:
                trigger_price = 0
            
            if buy_sell == "buy":
                t_type=session.BUY
            elif buy_sell == "sell":
                t_type=session.SELL
            
            if exchange == "NSE":
                exchange = session.NSE
            elif exchange == "NFO":
                exchange = session.NFO
            elif exchange == "BSE":
                exchange = session.BSE
            elif exchange == "BFO":
                exchange = session.BFO
                
            if product == "MIS":
                product_type=session.INTRA
            elif product == "NRML":
                product_type=session.MARGIN
                
            if order_type == "market":
                o_type=session.MARKET
            elif order_type == "limit":
                o_type=session.LIMIT
            elif order_type == "stoploss":
                o_type=session.SL
            

            try:
                order = session.place_order(tag=tag,
                                            transaction_type=t_type,
                                            exchange_segment=exchange,
                                            product_type=product_type,
                                            order_type=o_type,
                                            security_id=str(symbol.exchange_token),
                                            quantity=quantity,
                                            price=price,
                                            trigger_price=trigger_price)
                
                logging.info("Order id: {}".format(order))
    
                print("order id : " + order)
    
            except Exception as e:
                logging.info("Error placing order: {}".format(e))

        
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 10:56:42 2023

@author: Yugenderan
"""

from kiteconnect import KiteConnect
import math



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
        self.live = client_data['live']
        self.access_token = client_data['access_token']
        self.capital = client_data[strategy]
        
        
        
        
class General:     
    ## Function to generate Zerodha trading session
    def session_zerodha(user, clients):
        '''Create New Kite Session'''
        kite = KiteConnect(api_key=clients[user].api_key)
        kite.set_access_token(clients[user].access_token)
        return kite
    ###########################################################################
    ##function to round off to strike difference
    def round_multiple(number, multiplier):
        '''funtion to round off the number to nearest multiplier value'''
        return round(multiplier * round(number/multiplier),2)
    ###########################################################################
    def round_up(n, decimals=2):
        multiplier = 10 ** decimals
        return math.ceil(n * multiplier) / multiplier
    ###########################################################################    
    def round_down(n, decimals=2):
        multiplier = 10 ** decimals
        return math.floor(n * multiplier) / multiplier
    ###########################################################################  
    ##function to round up to strike difference
    def roundup_multiple(number, multiplier):
        '''funtion to round off the number to nearest multiplier value'''
        return round(multiplier * math.ceil(number/multiplier),2)

    ###########################################################################  
    ##function to round down to strike difference
    def rounddown_multiple(number, multiplier):
        '''funtion to round off the number to nearest multiplier value'''
        return round(multiplier * math.floor(number/multiplier),2)
 
    ###########################################################################
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

            self.quantity = order_quantity
            self.remaining_quantity = remaining_quantity

        return (order_quantity, remaining_quantity)
    ###########################################################################

    '''
    example:

    total_quantity = 20000
    max_quantity = 1750
    remaining_quantity = total_quantity

    quantity = OrderSlicing()


    while remaining_quantity != 0 :
        order_quantity, remaining_quantity = quantity.orderslicing(total_quantity, max_quantity, remaining_quantity)
        '''


    ###########################################################################

    def position_size(self, price, risk_value, lot_size):
        ''' Calculates Position size for the capital'''
        quantity = risk_value / price
        quantity = lot_size * round(quantity/lot_size)
        return quantity
    ###########################################################################
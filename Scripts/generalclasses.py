# -*- coding: utf-8 -*-
"""
Created on Tue Feb 14 14:43:49 2023

@author: Yugenderan
"""

###############################################################################       
class General:     
    ##function to round off to strike difference
    def round_multiple(number, multiplier):
        '''funtion to round off the number to nearest multiplier value'''
        return round(multiplier * round(number/multiplier),2)
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
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)


###############################################################################
# Changing Current Working Directory
#cwd = os.chdir("D:\\Zerodha API TEST\\1_account_authorization")
###############################################################################

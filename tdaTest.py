## API libraries
import sys, tweepy
import paralleldots
from selenium import webdriver
from tda import auth, client
from tda.orders.equities import equity_buy_limit
from tda.orders.common import Duration, Session
from twilio.rest import Client
## System / Other
import time
import config
import json
import math
from datetime import datetime
## Debug
import pprint
import config

## TDA Auth
try:
    c = auth.client_from_token_file(config.token_path, config.api_key)
except FileNotFoundError:
    with webdriver.Chrome(executable_path='./chromedriver.exe') as driver:
        c = auth.client_from_login_flow(driver, config.api_key, config.redirect_uri, config.token_path)



## GET OPTIONS CHAIN FOR 0DTE 0 to 2 points OTM
print(c.get_quote('SPY'))
#quote = c.get_quote('SPY')
# point_itm_1 = point_otm_2 = int(quote.json().get("SPY").get("lastPrice"))
# print(point_itm_1)
# point_otm_1 = int(quote.json().get("SPY").get("lastPrice") + 1)
# print(point_otm_1)
# point_otm_2 = int(quote.json().get("SPY").get("lastPrice") + 2)
# print(point_otm_2)
# #datetime.now() + timedelta(days=1) 
# res = c.get_option_chain('SPY', contract_type=c.Options.ContractType.CALL, strike=point_otm_1, strike_from_date=datetime.now(), strike_to_date=datetime.now())
# print(json.dumps(res.json(), indent=4))


# res = c.get_option_chain("AAPL")
# file1 = open("myfile.txt","a")#append mode 
# file1.write(json.dumps(res.json(), indent=4)) 
# file1.close() 
# print("DONE")
# res = json.loads(json.dumps(res.json()))
# print(res.get("putExpDateMap").get("2021-03-26:5").get("60.0")[0].get("symbol"))
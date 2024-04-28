## API libraries
import sys, tweepy
import paralleldots
from selenium import webdriver
from tda import auth, client
from tda.orders.equities import equity_buy_limit
from tda.orders.common import Duration, Session
#from twilio.rest import Client
## System / Other
import time
import config
import json
import math
from datetime import datetime
## Debug
import pprint

## Sentiment Auth
paralleldots.set_api_key(config.para_dot_key)
paralleldots.get_api_key()

## Twitter Auth
consumer_key = config.twi_con_key
consumer_secret = config.twi_con_key_s
access_token = config.twi_acc_tok
access_secret = config.twi_acc_sec

## Twitter Object Creation
twi_auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
twi_auth.set_access_token(access_token, access_secret)
client = tweepy.API(twi_auth, wait_on_rate_limit=True)

## TDA Auth
try:
    tda_c = auth.client_from_token_file(config.token_path, config.api_key)
except FileNotFoundError:
    with webdriver.Chrome(executable_path='./chromedriver.exe') as driver:
        tda_c = auth.client_from_login_flow(driver, config.api_key, config.redirect_uri, config.token_path)


## Variables to track
user = "CitronResearch"
#user = "DanZanger"
previous_tweet = ""
latest_tweet   = ""


## Twilio
#client = Client(config.twilio_account_sid, config.twilio_auth_token)


new_run = True
## Creates a new order: buy limit, sell limit or stop loss -<trail>%
# EXAMPLE: buyComplex("TSLA", 5)
# ticker: <String>; "TSLA"
# trail: <Integer>; 5
def buyComplex(ticker, trail):
    ticker = ticker.upper()
    print("Ticker = " + ticker)
    ## Prevent Purchasing on First Run
    if(new_run == True): 
        print("NEW RUN CANCEL PURCHASE LOGIC")
        return

    ## Get quote for found ticker
    res_ticker_info = tda_c.get_quotes(ticker)
    print("Quote = $", json.dumps(res_ticker_info.json().get(ticker).get("askPrice"), indent=4))
    ticker_ask_price = float(json.dumps(res_ticker_info.json().get(ticker).get("askPrice")))
    
    ## Check what my buying power is
    res_account_info = tda_c.get_account(config.tda_account)
    print("== Account info ==")
    tda_cash_balance = float(json.dumps( res_account_info.json().get("securitiesAccount").get("projectedBalances").get("cashAvailableForTrading")))
    print("Available Bal: $" + str(tda_cash_balance))

    ## Check how many shares I can purchase
    buy_limit  = round(ticker_ask_price*1.02, 2)
    sell_limit = round(ticker_ask_price*1.22, 2)
    tda_share_buy_power = math.floor(tda_cash_balance / buy_limit )
    print("Buyable share count: " + str(tda_share_buy_power))

    ## If I cannot buy any shares stop the function
    if(tda_share_buy_power < 1):
        print("Not enough funds available to purchase this ticker")
        return

    ## Create complex order template
    #NORMAL, #SEAMLESS
    order_template = {
        "orderStrategyType": "TRIGGER",
        "session": "NORMAL",
        "duration": "GOOD_TILL_CANCEL",
        "orderType": "LIMIT",
        "price": buy_limit,
        "orderLegCollection": [
            {
            "instruction": "BUY",
            "quantity": tda_share_buy_power,
            "instrument": {
                "assetType": "EQUITY",
                "symbol": ticker
            }
            }
        ],
        "childOrderStrategies": [
            {
            "orderStrategyType": "OCO",
            "childOrderStrategies": [
                {
                "orderStrategyType": "SINGLE",
                "session": "NORMAL",
                "duration": "GOOD_TILL_CANCEL",
                "orderType": "LIMIT",
                "price": sell_limit,
                "orderLegCollection": [
                    {
                    "instruction": "SELL",
                    "quantity": tda_share_buy_power,
                    "instrument": {
                        "assetType": "EQUITY",
                        "symbol": ticker
                    }
                    }
                ]
                },
                {
                    "orderType": "TRAILING_STOP",
                    "session": "NORMAL",
                    "stopPriceLinkBasis": "BID",
                    "stopPriceLinkType": "PERCENT",
                    "stopPriceOffset": trail,
                    "duration": "GOOD_TILL_CANCEL",
                    "orderStrategyType": "SINGLE",
                    "orderLegCollection": [
                        {
                        "instruction": "SELL",
                        "quantity": tda_share_buy_power,
                        "instrument": {
                            "symbol": ticker,
                            "assetType": "EQUITY"
                        }
                        }
                    ]
                }
            ]
            }
        ]
    }

    ## Submit Complex Order ##
    print(order_template)
    r = tda_c.place_order(config.tda_account, order_template)
    print("Created with status code: " + str(r))
    print("Reason: " + str( r.content ))

    ## STATUS CODES ##
    # 201 = Good
    # 400 = Bad (rounding error must be rounded 2d)
    # 500 = Bad (Failed because of incorrect order structure) / generic fail code

while(True):
    ## Fetch Tweet and parse it
    api = tweepy.API(twi_auth)
    new_tweets = api.user_timeline(screen_name = user,count=1, tweet_mode="extended") # 1x RES per second is max over 15min period!
    print("Start Time =", datetime.now().strftime("%H:%M:%S"))
    
    try:
        latest_tweet = new_tweets[0].full_text
        print(new_tweets[0].full_text)
    except IndexError as err:
        print("Error with getting latest tweet! See below for details.")
        pprint.pprint(new_tweets)
        print(err)
        latest_tweet = previous_tweet

    if latest_tweet == previous_tweet:
        print("No new tweets")
    else:
        prev_prev_tweet = previous_tweet ## THIS WILL MOST LIKELY STILL CAUSE PROBLEMS SINCE PREV PREV ONLY GETS UPDATED AFTER BUY IS TOLD THE 2nd TIME!! Works for prev though but not prev prev
        previous_tweet = latest_tweet

        ## DEBUG ##
            #latest_tweet = "$CVLB same biz as $HIMS.  $CVLB would be at $140 at $HIMS multiple AND $CVLB growing 160% vs $HIMS 30% No need to editorialize..here is the Telemedicine chart.  Citron long $CVLB.  New presentation compelling "
            #latest_tweet = "It is opinion of Citron that $GME next move is obvious and easy to justify stock price.  They should buy $AIRI.  Listen to your customers..they like to gamble and they like video games. Esports Gambling - Great synergies....$GMBL could easily go to $50."
            ## TEST CASES ##
            #latest_tweet = "THIS IS WONDERFUL" #Positive sentiment with no ticker
            #latest_tweet = "$TSLA is wonderful $GME" #Chooses first best which is TSLA.
            #latest_tweet = "$GME sucks, but I am in love with how great $GMBL is."

        ## Get Sentiment
        sentiment = paralleldots.sentiment(latest_tweet)
        #print(sentiment)
            #print("Pos: " + str( sentiment.get("sentiment").get("positive") ))
            #print("Neg: " + str( sentiment.get("sentiment").get("negative") ))
            #print("Neu: " + str( sentiment.get("sentiment").get("neutral") ))
        if(sentiment.get("sentiment").get("positive") > sentiment.get("sentiment").get("negative") and sentiment.get("sentiment").get("positive") > sentiment.get("sentiment").get("neutral")):
            print("Sentiment is positive.")
            ticker_count = 0
            ticker = ""
            for index, x in enumerate(latest_tweet):
                if(x == "$" and latest_tweet[index+1].isalpha()):
                    ticker_count += 1 ## Keep track of total ticker count
                    if(len(ticker) < 1): ## Grab only the first ticker
                        ticker = latest_tweet[index:index+5]
            #print("Ticker counter = " + str(ticker_count))
            ticker = ticker.replace('$', '')
            ticker = ticker.replace(' ', '')
            if(ticker_count > 1):
                print("MULTIPLE TICKER LOGIC")
                ## STEP ONE   -> Make an array of sentences
                sentence_parsed_list = latest_tweet.split(".") 
                sentiment_parsed_list = []
                ## STEP TWO   -> If Sentence doesn't have a $ticker in it dump it
                for i in sentence_parsed_list:
                    if "$" in i:
                        sentiment_parsed_list.append(i+".")
                ## STEP THREE -> Put sentence in dictionary with key and positive sentiment value
                sentiment_dict = {}
                for i in sentiment_parsed_list:
                    sentiment = paralleldots.sentiment(i)
                    sentiment_dict[i] = float(sentiment.get("sentiment").get("positive"))
                ## STEP FOUR  -> Choose tweet with highest positive sentiment score and use that for buy logic
                # May need to check if this is above 50 to ensure top positive is actually positive
                print(sentiment_dict)
                top_sentiment_result = max(sentiment_dict, key=sentiment_dict.get)
                print("MAX OUT OF THAT DICT = " + top_sentiment_result)

                ## Right now I just use the first Ticker of Positive Sentence. Sort of Risky buy will prevent over fitting
                for index, x in enumerate(top_sentiment_result):
                    if(x == "$" and top_sentiment_result[index+1].isalpha()):
                        ticker = top_sentiment_result[index:index+5]
                        break
                ticker = ticker.replace('$', '')
                ticker = ticker.replace(' ', '')
                print(ticker)
                if ticker:
                    buyComplex(ticker, 7)
                else:
                    print("No ticker found")

                order_receipt = "Time = " + datetime.now().strftime("%H:%M:%S") + " Ticker = " + ticker
                #message = client.messages.create(body=order_receipt,from_=config.twilio_from,to=config.twilio_to)
                print(order_receipt)
                print("Order Time =", datetime.now().strftime("%H:%M:%S"))
            else:
                #Only one ticker and positive, buy it.
                if ticker:
                    buyComplex(ticker, 7)
                    order_receipt = "Time = " + datetime.now().strftime("%H:%M:%S") + " Ticker = " + ticker
                    print(order_receipt)
                    #message = client.messages.create(body=order_receipt,from_=config.twilio_from,to=config.twilio_to)
                else:
                    print("No ticker found")
        else:
            #Negative Sentiment, don't buy it.
            print("Sentiment is not positive.")
    new_run = False
    time.sleep(4)

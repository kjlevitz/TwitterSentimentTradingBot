import paralleldots
import config
## Sentiment Auth
paralleldots.set_api_key(config.para_dot_key)
paralleldots.get_api_key()

#sentiment = paralleldots.sentiment("HELLO WORLD")

import requests
import json
api_key  = config.para_dot_key
lang_code= "en"
response = requests.post( "https://apis.paralleldots.com/v4/sentiment", data= { "api_key": api_key, "text": "HELLO WORLD", "lang_code": lang_code } ).text
print(response)
#response = json.loads( response )
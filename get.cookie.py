#step 1 login to your LinkedIn account using a Google Chrome browser. 
#step 2 install dependencies on your local computer. 

!pip install requests
!pip install browser_cookie3
!pip install linkedin-api

#step 3 save the below script to your local computer and run the script

import requests
import browser_cookie3
import json

from linkedin_api import Linkedin
from pathlib import Path

cookiejar_simple = browser_cookie3.chrome(domain_name='.linkedin.com')

cookiejar = requests.cookies.RequestsCookieJar()

for cookie in cookiejar_simple:
    cookiejar.set(cookie.name, cookie.value)
   
cookies_txt = requests.utils.dict_from_cookiejar(cookiejar)  # turn cookiejar into dict
cookies_123 = requests.utils.cookiejar_from_dict(cookies_txt)


print(cookies_txt)


#result should be a printed cookie which you can now use in the main script job_search.py 

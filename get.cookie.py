#STEP 1. Login to your LinkedIn account using a Google Chrome browser. 
#STEP 2. Install the necessary dependencies on your local computer by running the following commands:
    pip install requests
    pip install browser_cookie3
    pip install linkedin-api
# STEP 3. Copy and paste the below and save in a py file on your local computer.

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


# STEP 4. Run the py file to retrieve your LinkedIn session cookies.

# Result:
# The result should be a printed cookie dictionary, which you can now use in the main script 'job_search.py'.

# Job Search Automation using Python and ChatGPT

This project automates the process of job searching by leveraging Python and the OpenAI API (ChatGPT) together with the free LinkedIn API. The LinkedIn API used in this project can be found [here](https://github.com/username/linkedin-api-project). 
This project scrapes job postings from LinkedIn, uses Chat GPT to categorise the jobs based on your specific criteria, and emails the results daily.
Read my article on Medium [here]( https://medium.com/@lauradillingamlspecialist/from-zero-coding-to-job-search-hero-how-i-used-chatgpt-and-python-to-automate-my-job-search-with-937f91cfe3a8). 

## Features
- Automated job search and filtering based on user-defined criteria.
- Utilises linkedin-api to get job data. 
- Utilises OpenAI's GPT-3.5-turbo model for categorising job postings.
- Sends a HTML report via email with categorised job listings.

## Installation

1. Clone the repository to your local machine or download the files directly.
2. Install the required Python packages:

   ```bash
   pip install -r requirements.txt

## Configuration

1. Locate the config.ini file in the root directory of this project and update it with your personal information (e.g., email settings, job search criteria).
2. In the job_search.py script, update the LINKEDIN_SESSION_COOKIE at line 29 with your personal LinkedIn session cookie. Detailed instructions on how to retrieve your personal cookie can be found in the get.cookie.py file included in this repository.
   

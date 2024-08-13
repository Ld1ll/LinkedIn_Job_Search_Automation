import requests
import browser_cookie3
import json
import datetime
import time
import pickle
import smtplib
import re


from configobj import ConfigObj
from openai import OpenAI
from linkedin_api import Linkedin
from itertools import combinations
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential )  # for exponential backoff
from tqdm import tqdm #for progress bar
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dataclasses import dataclass


CONFIG_PATH = 'config.ini'

PKL_PATH = 'job_ids.pkl'

LINKEDIN_SESSION_COOKIE = {YOUR.COOKIE.HERE.AS.DICT}

config = ConfigObj(CONFIG_PATH)

@dataclass
class UserProfile:
  USER_ID: str
  #LINKED_IN_SESSION_COOKIE: str
  OPENAI_API_KEY: str
  USER_EMAIL_SMTP_ADDRESS: str
  USER_EMAIL_SMTP_PORT: int
  USER_EMAIL_ADDRESS: str
  USER_EMAIL_LOGIN: str
  USER_EMAIL_PASSWORD: str
  DEST_EMAIL_ADDRESS: str
  SEARCH_KEYWORD: str
  SEARCH_LOCATION: str
  ASSESSMENT_CRITERIAS: str


def get_users_profiles(config):
  users_profiles = []


  for user_id in config:

    u_p = UserProfile(
                              USER_ID=user_id,
                              #LINKED_IN_SESSION_COOKIE=json.loads(config[user_id]['linked_in_session_cookie']),
                              OPENAI_API_KEY=config[user_id]['openai_api_key'],
                              USER_EMAIL_SMTP_ADDRESS=config[user_id]['user_email_smtp_server_address_port'].split(":")[0],
                              USER_EMAIL_SMTP_PORT=int(config[user_id]['user_email_smtp_server_address_port'].split(":")[1]),
                              USER_EMAIL_ADDRESS = config[user_id]['user_email_address'],
                              USER_EMAIL_LOGIN=config[user_id]['user_email_login'],
                              USER_EMAIL_PASSWORD=config[user_id]['user_email_password'],
                              DEST_EMAIL_ADDRESS=config[user_id]['dest_email_address'],
                              SEARCH_KEYWORD=config[user_id]['search_keyword'],
                              SEARCH_LOCATION=config[user_id]['search_location'],
                              ASSESSMENT_CRITERIAS=config[user_id]['assessment_criterias']
                            )
    users_profiles.append(u_p)
  return users_profiles


def init_api(session_cookie=LINKEDIN_SESSION_COOKIE):
  cookies_123 = requests.utils.cookiejar_from_dict(session_cookie)

  api = Linkedin("", "", cookies=cookies_123)

  return api


def extract_jop_postings(api, keywords, location_name):
  search_results = None

  try:
    search_results = api.search_jobs(keywords=keywords, location_name=location_name)
  except ValueError as e:
    print("API returned error --->", e)

  return search_results


def extract_job_ids(job_postings):
    job_ids = []
    for job in job_postings:
        entity_urn = job.get('entityUrn', '')
        split = entity_urn.split(':')
        if len(split) < 4:
            continue
        job_id = split[3]
        job_ids.append(job_id)

    return job_ids

# Define function to calculate token usage of each dictionary
def calculate_token_usage(dictionaries):
    return {i: len(json.dumps(d)) // 4 for i, d in enumerate(dictionaries)}

# Define function to send request with backoff
@retry(wait=wait_random_exponential(min=30, max=65), stop=stop_after_attempt(12))
def completion_with_backoff(**kwargs):
    return client.chat.completions.create(**kwargs)

def generate_html(jobs_assessed, today_date):
    # Calculate job statistics
    total_jobs = len(jobs_assessed)
    suitable_count = sum(1 for job in jobs_assessed if job.get('Job Rating', '').lower() == 'suitable')
    maybe_suitable_count = sum(1 for job in jobs_assessed if job.get('Job Rating', '').lower() == 'maybe suitable')
    not_suitable_count = sum(1 for job in jobs_assessed if job.get('Job Rating', '').lower() == 'not suitable')

    # Add the statistics at the top of the HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
            }}
            .job {{
                border: 1px solid #ddd;
                margin-bottom: 20px;
                padding: 10px;
                border-radius: 5px;
            }}
            .job h2 {{
                margin: 0 0 10px;
                font-size: 1.2em;
            }}
            .job p {{
                margin: 5px 0;
            }}
            .not-suitable {{
                color: red;
            }}
            .maybe-suitable {{
                color: orange;
            }}
            .suitable {{
                color: green;
            }}
            .reasons {{
                margin-left: 20px;
                list-style-type: disc;
            }}
            .stats {{
                margin-bottom: 20px;
                padding: 10px;
                border-radius: 5px;
                background-color: #f0f0f0;
            }}
            .stats h2 {{
                margin: 0;
                font-size: 1.5em;
            }}
            .stats p {{
                margin: 5px 0;
            }}
            .stats .suitable {{
                color: green;
            }}
            .stats .maybe-suitable {{
                color: orange;
            }}
            .stats .not-suitable {{
                color: red;
            }}
            .stats .total-jobs {{
                font-weight: bold;
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="stats">
            <h2>Jobs Assessed as of {today_date}</h2>
            <p class="total-jobs">Total jobs: {total_jobs}</p>
            <p class="suitable">Suitable: {suitable_count}</p>
            <p class="maybe-suitable">Maybe suitable: {maybe_suitable_count}</p>
            <p class="not-suitable">Not suitable: {not_suitable_count}</p>
        </div>
    """

    for job in jobs_assessed:
        # Safely get job details with default values if the key is missing
        date_listed = job.get('Date listed', 'N/A')
        job_rating = job.get('Job Rating', 'Unknown').lower().replace(' ', '-')
        job_title = job.get('Job Title', 'N/A')
        company = job.get('Company', 'N/A')
        link = job.get('Link', '#')
        description = job.get('Description', 'N/A')

        # Handle the reasons section based on the job rating
        reasons = job.get(
            f"Job is {job.get('Job Rating', 'Unknown')} because",
            description.split('\n')[1:]  # Default to splitting description if reasons not provided
        )

        html_content += f"""
        <div class="job">
            <h2>Job ID: {job.get('Job ID', 'N/A')}</h2>
            <p>Date Listed: {date_listed}</p>
            <p class="{job_rating}">Job Rating: {job.get('Job Rating', 'Unknown')}</p>
            <p>Job Title: {job_title}</p>
            <p>Company: {company}</p>
            <p>Link: <a href="{link}">{link}</a></p>
            <p>Description: {description}</p>
            <p>Job is {job.get('Job Rating', 'Unknown')} because:</p>
            <ul class="reasons">
        """
        for reason in reasons:
            if reason.strip():  # Only add non-empty reasons
                html_content += f"<li>{reason.strip()}</li>"

        html_content += """
            </ul>
        </div>
        """

    html_content += """
    </body>
    </html>
    """

    return html_content

def save_job_ids(user_id, job_ids):
  data = {}
  try:
    with open(PKL_PATH, 'rb') as f:
      data = pickle.load(f)
  except FileNotFoundError:
    pass
  with open( PKL_PATH, 'wb') as f:
    data[user_id] = job_ids
    pickle.dump(data, f)

def load_job_ids(user_id):
  with open(PKL_PATH, 'rb') as f:
    job_ids = pickle.load(f)
  return job_ids.get(user_id,[])

def save_html_output(filename, html_content):
  with open(filename, 'w') as f:
    f.write(html_content)

def create_and_send_email(email_from, email_to, email_subject, html_email_content, smtp_server, smtp_port, username, password):
  # Create message container - the correct MIME type is multipart/alternative.
  msg = MIMEMultipart('alternative')
  msg['Subject'] = email_subject
  msg['From'] = email_from
  msg['To'] = email_to

  # Attach the HTML email content to the message
  html_part = MIMEText(html_email_content, 'html')
  msg.attach(html_part)

  # Send the message via local SMTP server.
  mail = smtplib.SMTP(smtp_server, smtp_port)

  mail.ehlo()

  mail.starttls()

  mail.login(username, password)
  mail.sendmail(email_from, email_to, msg.as_string())
  mail.quit()


if __name__ == "__main__":

  for up in get_users_profiles(config):

    api = init_api()

    search_results = extract_jop_postings(api, up.SEARCH_KEYWORD, up.SEARCH_LOCATION)

    print(up.USER_ID, up.SEARCH_KEYWORD, up.SEARCH_LOCATION, search_results)

    if search_results:
      # Fetch already processed job IDs
      print(f'Fetching job IDs from local drive...')
      try:
        job_ids_processed = load_job_ids(up.USER_ID)
        print(f'Fetched {len(job_ids_processed)} job IDs...')
      except FileNotFoundError:
        job_ids_processed = []

      # Extract job IDs, passing the search results to the function
      job_ids = extract_job_ids(search_results)

      # Filter out job IDs that have already been processed
      job_ids = [job_id for job_id in job_ids if job_id not in job_ids_processed]

      # Save the new job IDs
      print(f'Saving {len(job_ids)} new job IDs to local drive...')
      save_job_ids(up.USER_ID, job_ids_processed + job_ids)

      print(f"fetching {len(job_ids)} job IDs from LinkedIn")

      # Initialize list to store all job data dictionaries
      all_job_data = []

      # Loop through each job ID to extract related job data
      print(f"fetching job posting details from LinkedIn...")
      for i in tqdm(range(len(job_ids))):
        job_id = job_ids[i]
        try:
            job_data = api.get_job(job_id)
            company_details = job_data['companyDetails'].get('com.linkedin.voyager.deco.jobs.web.shared.WebCompactJobPostingCompany', {}).get('companyResolutionResult', {}).get('name', None)
            job_description = job_data['description'].get('text', None)
            job_title = job_data['title']
            location = job_data['formattedLocation']
            listed_at_timestamp = job_data['listedAt']
            date_listed_datetime_format = datetime.datetime.fromtimestamp(listed_at_timestamp / 1000)
            date_listed = date_listed_datetime_format.isoformat()
            job_posting_link = f'https://www.linkedin.com/jobs/view/{job_id}/'

            # Create dictionary containing job data
            required_job_data = {
                'job_id': job_id,
                'company_details': company_details,
                'job_description': job_description,
                'job_title': job_title,
                'location': location,
                'date_listed': date_listed,
                'job_posting_link': job_posting_link
            }

            # Add the job data dictionary to the list
            all_job_data.append(required_job_data)

        except KeyError as e:
            print(f"KeyError: {e} - Skipping job ID {job_id}")
        except Exception as e:
            print(f"Error: {e} - Skipping job ID {job_id}")

      print(f"fetched {len(all_job_data)} job postings")


      # Call function to calculate token usage of each dictionary
      token_usages = calculate_token_usage(all_job_data)

      # Sort dictionaries based on token usage (ascending order)
      sorted_indices = sorted(token_usages, key=lambda x: token_usages[x])

      # Initialize variables
      batches = []
      current_batch = []
      current_token_count = 0
      token_limit = 10000

      # Pack dictionaries greedily into batches
      #print(sorted_indices)
      for idx in sorted_indices:
          token_usage = token_usages[idx]
          if current_token_count + token_usage <= token_limit:
              #print(f"adding [{idx}] with token count: {token_usage} to current batch... tokens left in batch: {token_limit-current_token_count - token_usage} ")
              current_batch.append(all_job_data[idx])
              current_token_count += token_usage
          else:
              # Add current_batch to batches and reset variables
              #print(f"adding batch with {len(current_batch)} jobs and total token count {current_token_count}")
              batches.append(current_batch)
              current_batch = [all_job_data[idx]]
              current_token_count = token_usage
              #print(f"creating new batch populated with [{idx}] with token count: {token_usage}... tokens left in new batch: {token_limit-current_token_count}")

      # Add the last batch if any dictionaries are left
      if current_batch:
          if current_token_count <= token_limit:
            #print(f"adding the last batch with {len(current_batch)} jobs and the total token count of {current_token_count}")
            batches.append(current_batch)
          else:
            print(f"failed to add batch with {len(current_batch)} jobs as total token count of {current_token_count} exceeds the limit of {token_limit}")

      # Initialize OpenAI client
      client = OpenAI(api_key=up.OPENAI_API_KEY)

      # Define the system message for the API
      system_message = {
          "role": "system",
          "content": f'''You are a highly skilled career coach and recruitment specialist with over 20 years of experience. You will receive data in relation to job postings on LinkedIn and your role is to assess each job provided to determine if the role would be a good fit for the candidate.
          You are tasked with providing a response categorising each job provided into ‘Suitable’, ‘Maybe Suitable’ or ‘Not Suitable’:

         {up.ASSESSMENT_CRITERIAS}

          **Example structure of job data you will receive:**
          'job_id': job_id,
          'company_details': company_details,
          'job_description': job_description,
          'job_title': job_title,
          'location': location,
          'date_listed': date_listed,
          'job_posting_link': job_posting_link'''
      }



      # Process each batch
      print(f"sending batches with job data to ChatGPT :)")
      responses = []

      for i in tqdm(range(len(batches))):
          batch = batches[i]
          # Create batch string
          batch_str = json.dumps(batch)
          job_count = len(batch)
          #print(job_count)

          # Define user message with batch data
          user_message = {
              "role": "user",
              "content": f'''Please assess jobs based on the provided data {batch_str} and categorize each job as Suitable, Maybe Suitable, or not Suitable. Provide output as a list of dictionaries whereby each job from the list represents a new dictionary in the list.
              The dictionary for each job assessed should be structured in the following way:
              jobs_assessed = {{
              Job ID: job id here,
              Date listed: date_listed here,
              Job Rating: Suitable or Maybe Suitable or Not Suitable,
              Job Title: title here,
              Company: company name here or 'N/A' if not provided,
              Link: job posting link here,
              Description: one sentence summary of job listing.
              Job is (insert suitable or maybe suitable or not suitable) because: dot point reasons for why job is suitable or maybe suitable or not suitable.
              }}
              Please make sure that the output is in JSON format and is always a list of dictionaries (even if there is only one job in the request). Please make sure you provide a job assessment for every job provided i.e. I have provided you with {job_count} jobs, so there should be {job_count} job assessments included in the output.
              '''
          }


          # Send request to OpenAI API
          response = completion_with_backoff(
              model="gpt-3.5-turbo",
              temperature=0,
              response_format={"type": "json_object"},
              messages=[
                  system_message,
                  user_message
              ]
          )

          # Print or process the response
          content = response.choices[0].message.content
          content = json.loads(content)
          print(content)
          responses.extend(content['jobs_assessed'])
          #print(f"Batch {i+1} Response:")
          #print(content)
          #print()
      print(f"finished with ChatGPT after processing {len(batches)} batches")
      #print(responses)
      print(f"{len(responses)} jobs assessed by Chat GPT")


    if responses:
      # Custom order for job ratings
      rating_order = {
          "suitable": 0,
          "maybe suitable": 1,
          "not suitable": 2,
          "Suitable": 0,
          "Maybe Suitable": 1,
          "Maybe suitable": 1,
          "Not suitable": 2
      }

      # Sort the responses based on the custom order
      sorted_responses = sorted(responses, key=lambda x: rating_order.get(x['Job Rating'].strip().lower(), 3))

      # Get today's date in YYYY-MM-DD format
      today_date = datetime.datetime.now().strftime('%Y-%m-%d')

      # Generate HTML Output
      html_output = generate_html(sorted_responses, today_date)

      print(f"Sending Email from {up.USER_EMAIL_ADDRESS} --> {up.DEST_EMAIL_ADDRESS}...")

      create_and_send_email( email_from = up.USER_EMAIL_ADDRESS,
                            email_to = up.DEST_EMAIL_ADDRESS,
                            email_subject = f'new jobs as of {today_date}',
                            html_email_content = html_output,
                            smtp_server = up.USER_EMAIL_SMTP_ADDRESS,
                            smtp_port = up.USER_EMAIL_SMTP_PORT,
                            username = up.USER_EMAIL_ADDRESS,
                            password = up.USER_EMAIL_PASSWORD )
      print(f"Email sent successfully!")

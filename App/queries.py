#%%
import requests
import json
import os
import sqlite3
import uuid

from utils import json_get_key

import logging
logging.basicConfig(filename="LOG.log",
                    filemode="a",
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

def get_token_usage():
    '''
    Returns the number of used tokens, and the total number of available tokens during this period
    for the TheirStack job API.
    '''

    TOKEN = json_get_key("keys.json", "THEIRSTACK_TOKEN") #os.getenv("THEIR_STACK_TOKEN")

    try:
        res = requests.get("https://api.theirstack.com/v0/billing/credit-balance",
            headers={'Authorization': f"Bearer {TOKEN}"})
    except Exception as e:
        logging.info(e)
    
    if res.status_code == 200:
        content = json.loads(res.content)
        return (content["used_api_credits"], content["api_credits"])
    else:
        if res.status_code == 401: logging.info("TheirStack gave status code 401: Invalid authentication credentials.")
        elif res.status_code == 402: logging.info("TheirStack gave status code 402: Payment Required (you probably exceeded the API limit this month).")
        elif res.status_code == 404: logging.info("TheirStack gave status code 404: Not Found.")
        elif res.status_code == 405: logging.info("TheirStack gave status code 405: Method not allowed (you probably used some outdated endpoint).")
        elif res.status_code == 422: logging.info("TheirStack gave status code 422: Unprocessable Entity")
        else: logging.warning(f"TheirStack gave unknown status code {res.status_code}")

        return ("-","-")
    
    


def get_jobs(limit=2, masked_data=True, save_locally=True):
    '''
    Retrieves jobs with the pre-specified query.
    '''
    
    HEADERS = {
        'Content-Type': "application/json",
        'Authorization': f"Bearer {json_get_key("keys.json", "THEIRSTACK_TOKEN")}"
    }

    # Retrieve saved job id's, so that they can be excluded from the job query below.
    conn = sqlite3.connect("db.sqlite", isolation_level=None)
    job_ids = [i[0] for i in conn.execute("SELECT id_theirstack from jobs;").fetchall()]

    # Get locations for processing below
    locations = json_get_key("keys.json", "locations")

    PAYLOAD = {
        'page': 0,
        'limit': limit,
        'job_country_code_or': ['SE'],
        'posted_at_max_age_days': 30,
        'blur_company_data': masked_data, # set to false in order to get full information (when enabled it does not consume API token)
        'job_title_or': json_get_key("keys.json", "job_title_or"), #['Data Scientist', 'Data Engineer', 'Data Analyst', 'Dataingenjör', 'Machine Learning Engineer'],
        'job_title_not': json_get_key("keys.json", "job_title_not"), #['Senior'],
        #'job_seniority_or': ['junior'],
        'job_id_not': job_ids,
        'job_location_or': [locations[key][1] for key in locations if locations[key][0] == 1]
        # 'job_location_or': [{'id': '2673722'}, {'id': '2673730'}, {'id': '2673723'},
        #                     {'id': '2694759'}, {'id': '2694762'}, {'id': '2688367'}, {'id': '2688368'}]
    }

    logging.info(f"Attempting job search with payload:\n\n\n{PAYLOAD}\n\n\n")

    try:
        res = requests.post("https://api.theirstack.com/v1/jobs/search",
                            headers=HEADERS,
                            json=PAYLOAD
                            )
    except Exception as e:
        logging.info(e)
    
    # Log the status code
    
    if res.status_code != 200:
        if res.status_code == 401: logging.info("TheirStack gave status code 401: Invalid authentication credentials.")
        elif res.status_code == 402: logging.info("TheirStack gave status code 402: Payment Required (you probably exceeded the API limit this month).")
        elif res.status_code == 404: logging.info("TheirStack gave status code 404: Not Found.")
        elif res.status_code == 405: logging.info("TheirStack gave status code 405: Method not allowed (you probably used some outdated endpoint).")
        elif res.status_code == 422: logging.info("TheirStack gave status code 422: Unprocessable Entity")
        else: logging.warning(f"TheirStack gave unknown status code {res.status_code}")
        
        # Shut down
        #get_token_usage()
        return None
    elif res.status_code == 200: pass

    
    # Present the retrieved jobs, and save them to the database file.
    content = json.loads(res.content)
    logging.info(f"Received content:\n\n{content}\n\n")
    if len(content["data"]) == 0:
        logging.info("No jobs were found.")
        #get_token_usage()
        return None
    else:
        pass
        #print("The following job(s) were found:")

    for job in content["data"]:
        #print("-----------------------------------------------")
        #print("\n".join([job["job_title"], job["company"], job["location"]]))
        
        #VALUES = "({id}, '{job_title}', '{url}', '{date_posted}', {has_blurred_data}, '{company}', '{final_url}', '{source_url}', '{location}', {remote}, {hybrid}, '{salary_string}', '{seniority}', '{company_domain}', {reposted}, '{date_reposted}', {technology_slugs}, '{description}')".format(id=job["id"], job_title=job["job_title"], url=job["url"], date_posted=job["date_posted"], has_blurred_data=job["has_blurred_data"], company=job["company"], final_url=job["final_url"], source_url=job["source_url"], location=job["source_url"], remote=job["remote"], hybrid=job["hybrid"], salary_string=job["salary_string"], seniority=job["seniority"], company_domain=job["company_domain"], reposted=job["reposted"], date_reposted=job["date_reposted"], technology_slugs=f"{job["technology_slugs"]}", description=job["description"])

        # Insert job in database
        if save_locally:
            conn = sqlite3.connect("db.sqlite", isolation_level=None)
            conn.execute("INSERT INTO jobs (id, id_theirstack, job_title, url, date_posted, has_blurred_data, company, final_url, source_url, location, remote, hybrid, salary_string, seniority, company_domain, reposted, date_reposted, employment_statuses, technology_slugs, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                        (uuid.uuid4().__str__(),
                        job["id"],
                        job["job_title"],
                        job["url"],
                        job["date_posted"],
                        job["has_blurred_data"],
                        job["company"],
                        job["final_url"],
                        job["source_url"],
                        job["location"],
                        job["remote"],
                        job["hybrid"],
                        job["salary_string"],
                        job["seniority"],
                        job["company_domain"],
                        job["reposted"],
                        job["date_reposted"],
                        json.dumps(job["employment_statuses"]),
                        json.dumps(job["technology_slugs"]),
                        job["description"])).fetchall()

        # Insert company in database if not already exists
        ## I'm ignoring this for now, since it doesn't appear very useful to maintain information of specific companies.

    #get_token_usage()


#%%
import requests
import json
import os
import sqlite3

from dotenv import load_dotenv
load_dotenv()
from utils import json_get_key

def get_token_usage():
    '''
    Returns the number of used tokens, and the total number of available tokens during this period
    for the TheirStack job API.
    '''

    TOKEN = json_get_key("keys.json", "THEIRSTACK_TOKEN") #os.getenv("THEIR_STACK_TOKEN")

    res = requests.get("https://api.theirstack.com/v0/users/me",
        headers={'Authorization': f"Bearer {TOKEN}"})
    
    if res.status_code != 200:
        raise ValueError(f"Failed to retrieve user info. The request returned status code {res.status_code}")
    
    content = json.loads(res.content)
    print(f"\nAPI credits used: {content["team"]["api_credits_used_current_period"]}/{content["team"]["api_credits"]}")

    return (content["team"]["api_credits_used_current_period"], content["team"]["api_credits"])


def get_jobs(limit=7, masked_data=True, theirstack_token=None):
    '''
    Retrieves jobs with the pre-specified query.
    '''
    
    # If no token is given
    if not theirstack_token: return None

    HEADERS = {
        'Content-Type': "application/json",
        'Authorization': f"Bearer {theirstack_token}"
    }

    # Retrieve saved job id's, so that they can be excluded from the job query below.
    conn = sqlite3.connect("db.sqlite", isolation_level=None)
    job_ids = [i[0] for i in conn.execute("SELECT id from jobs;").fetchall()]

    PAYLOAD = {
        'page': 0,
        'limit': limit,
        'job_country_code_or': ['SE'],
        'posted_at_max_age_days': 30,
        'blur_company_data': masked_data, # set to false in order to get full information (when enabled it does not consume API token)
        'job_title_or': ['Data Scientist', 'Data Engineer', 'Data Analyst', 'Dataingenjör', 'Machine Learning Engineer'],
        'job_title_not': ['Senior'],
        #'job_seniority_or': ['junior'],
        'job_id_not': job_ids,
        'job_location_or': [{'id': '2673722'}, {'id': '2673730'}, {'id': '2673723'},
                            {'id': '2694759'}, {'id': '2694762'}, {'id': '2688367'}, {'id': '2688368'}]
    }

    res = requests.post("https://api.theirstack.com/v1/jobs/search",
                        headers=HEADERS,
                        json=PAYLOAD
                        )
    
    if res.status_code != 200:
        if res.status_code == 402: print("Status code 402: Payment Required (you probably exceeded the API limit this month).")
        elif res.status_code == 405: print("Status code 405: Method not allowed (you probably used some outdated endpoint).")
        else: print(f"Unknown status code {res.status_code}")
        
        # Shut down
        get_token_usage()
        return None
    elif res.status_code == 200: pass

    
    # Present the retrieved jobs, and save them to the database file.
    content = json.loads(res.content)
    if len(content["data"]) == 0:
        print("No jobs were found.")
        get_token_usage()
        return None
    else:
        print("The following job(s) were found:")

    for job in content["data"]:
        print("-----------------------------------------------")
        print("\n".join([job["job_title"], job["company"], job["location"]]))
        
        #VALUES = "({id}, '{job_title}', '{url}', '{date_posted}', {has_blurred_data}, '{company}', '{final_url}', '{source_url}', '{location}', {remote}, {hybrid}, '{salary_string}', '{seniority}', '{company_domain}', {reposted}, '{date_reposted}', {technology_slugs}, '{description}')".format(id=job["id"], job_title=job["job_title"], url=job["url"], date_posted=job["date_posted"], has_blurred_data=job["has_blurred_data"], company=job["company"], final_url=job["final_url"], source_url=job["source_url"], location=job["source_url"], remote=job["remote"], hybrid=job["hybrid"], salary_string=job["salary_string"], seniority=job["seniority"], company_domain=job["company_domain"], reposted=job["reposted"], date_reposted=job["date_reposted"], technology_slugs=f"{job["technology_slugs"]}", description=job["description"])

        # Insert job in database
        if not masked_data:
            conn = sqlite3.connect("job_search_database.sqlite", isolation_level=None)
            conn.execute("INSERT INTO jobs (id, job_title, url, date_posted, has_blurred_data, company, final_url, source_url, location, remote, hybrid, salary_string, seniority, company_domain, reposted, date_reposted, employment_statuses, technology_slugs, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                        (job["id"],
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

    get_token_usage()


def destroy_database():
    '''Drop the jobs table. VERY BAD! BE CAREFUL!'''

    print("You are about to DROP the jobs table. THIS IS DANGEROUS!")
    print("It might contain important data, so please be careful!")
    responses = []
    
    while True:
        inp = input("Are you sure? [Y/n]>")

        if inp == "Y": responses += "Y"
        elif inp == "n":
            print("Destruction aborted")
            break

        if responses == ["Y", "Y", "Y", "Y"]:
            print("Ok, you seem really really sure. Let's drop the jobs table.")

            conn = sqlite3.connect("job_search_database.sqlite", isolation_level=None)
            conn.execute("DROP TABLE IF EXISTS jobs;")

            break

def build_database():
    '''For building the database, particularly the jobs table.'''

    conn = sqlite3.connect("job_search_database.sqlite", isolation_level=None)
    with open("build_database.sql", "r") as f:
        sql_script = f.read()
        for statement in sql_script.split(";"):
            conn.execute(statement)
# %%

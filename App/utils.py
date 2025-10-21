import os
import sys
import sqlite3

import logging
logging.basicConfig(filename="LOGS.log",
                    filemode="a",
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
logging.info("Started utils")


def run_sql(db="db.sqlite", script=None, string=None):
    '''
    Executes sql on the database.
    Wraps all the hassle of connection etc.
    
    Give either the path to a .sql script, or a direct sql string.
    '''
    # Error handling
    if script and string:
        raise ValueError("Both script and string were passed. Expected exactly one.")

    try:
        with sqlite3.connect(db) as conn:
            print("DB Connection established")
            # Open a cursor to perform database operations

            if script:
                with open(script, "r") as f:
                    for command in f.read().split(";"):
                        conn.execute(command)
            elif string:
                resp = conn.execute(string)
        
            try:
                return resp.fetchall()
            except:
                #print("Failed to fetch rows (might be expected).")
                return None
            
            # The transaction is committed automatically when the 'with' block exits in psycopg (v3)
    except Exception as e:
        logging.info(e)
        print("Connection failed.")
        print(e)
    

def build_db(db="db.sqlite"):
    '''
    Build the database tables that don't exist.
    '''
    try:
        with sqlite3.connect(db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id integer PRIMARY KEY,
                    job_title text,
                    url text,
                    date_posted text,
                    has_blurred_data boolean,
                    company text,
                    final_url text,
                    source_url text,
                    location text,
                    remote boolean,
                    hybrid boolean,
                    salary_string text,
                    seniority text,
                    company_domain text,
                    reposted boolean,
                    date_reposted text,
                    employment_statuses text,
                    technology_slugs text,
                    description text,

                    relevance_score integer,
                    status text default '---',
                    comment text default ''
                );
            ''')
    except Exception as e:
        logging.info(e)



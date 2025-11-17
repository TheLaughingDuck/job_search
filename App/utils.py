import os
import sys
import sqlite3
import uuid

import logging
logging.basicConfig(filename="LOG.log",
                    filemode="a",
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)


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
                    id text PRIMARY KEY,
                    id_theirstack integer DEFAULT NULL,
                    job_title text,
                    url text,
                    date_posted text,
                    has_blurred_data boolean DEFAULT FALSE,
                    company text,
                    final_url text,
                    source_url text,
                    location text,
                    remote boolean DEFAULT FALSE,
                    hybrid boolean DEFAULT FALSE,
                    salary_string text,
                    seniority text,
                    company_domain text,
                    reposted boolean DEFAULT FALSE,
                    date_reposted text,
                    employment_statuses text,
                    technology_slugs text,
                    description text,

                    relevance text default '---',
                    status text default '---',
                    comment text default ''
                );
            ''')
    except Exception as e:
        logging.info(e)
    

    try:
        # If there are no jobs in the database, add some example jobs
        if len(conn.execute("SELECT id FROM jobs;").fetchall()) == 0:

            conn.execute(f"INSERT INTO jobs (id, job_title, company, date_posted, status, relevance, description, location, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                         (uuid.uuid4().__str__(), 'Pikeman', 'Alfred Nobleman', '1653-02-18', '---', 'Relevant', 'We need a strong, dependable, and expendable man to hold a long pike and point it against the enemeny. Similar previous experience is highly preferred.', 'Switzerland', 'Seems like a good job with nice career prospects.'))
            
            conn.execute(f"INSERT INTO jobs (id, job_title, company, date_posted, status, relevance, description, location, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                         (uuid.uuid4().__str__(), 'Receptionist', 'The shady hotel by the station', '2013-05-29', 'Applied', 'Relevant', 'If you can breathe and talk, you are perfect for this job.', 'Stockholm', 'Good place to work.'))
            
            conn.execute(f"INSERT INTO jobs (id, job_title, company, date_posted, status, relevance, description, location, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                         (uuid.uuid4().__str__(), 'Player Character', 'Adventurer\'s Guild', '357-01-07', 'Rejected', 'Perfect', 'We need a level 5+ cleric for our party, because nobody wants to be the party healer. Pay will be discussed after you survive 2 sessions.', 'City of Blades', 'They rejected me because I named my character Claire Ike.'))
            
            conn.commit()
    except Exception as e:
        logging.info(e)




import json

def json_get_key(fp, key):
    '''
    Opens a JSON file at `fp`, returns the value for `key`.
    If the key doesn't exist, adds it with a null value (None) and updates the file.
    '''
    
    try:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        data = {}

    # If key doesn't exist, set it to None and update the file
    if key not in data:
        data[key] = ""
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    return data[key]

def json_set_key(fp, key, val):
    '''
    Opens a JSON file at `fp`, and sets the value `val` for `key`.
    If the key doesn't exist, adds it with a null value (None) and updates the file.
    '''
    
    # Load the JSON file (create empty if it doesn't exist)
    try:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        data = {}

    # If key doesn't exist, set it to `val` and update the file
    data[key] = val
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def create_keys_file(fp="keys.json"):
    '''
    Create the keys file if it does not already exist.
    '''

    # Check if it exists
    if not os.path.isfile(fp):
        keys = {
            "THEIRSTACK_TOKEN": "exampleexampleexample",
            "job_title_or": [
                "Receptionist,Painter,Data Scientist"
            ],
            "job_title_not": [
                "Senior"
            ],
            "limit": 5,
            "locations": {
                "Stockholm": [0, {'id': '2673730'}],
                "Stockholms Lan": [0, {'id': '2673722'}],
                "Stockholms Kommun": [0, {'id': '2673723'}],
                "Ostergotland Lan": [0, {'id': '2685867'}],
                "Linkoping": [0, {'id': '2694762'}],
                "Linkopings Kommun": [0, {'id': '2694759'}],
                "Norrkoping": [0, {'id': '2688368'}],
                "Norrkopings Kommun": [0, {'id': '2688367'}]
            },
            "locations_v2": [],

            # The column widths, in the order in which the columns appear (left to right) (see 'app.pyw')
            "treeview_column_widths": [228, 128, 130, 76, 117, 559]
        }

        # Save the keys file
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(keys, f, indent=4)

    else:
        pass
        #logging.info("Attempted to create 'keys.json': it already exists.")
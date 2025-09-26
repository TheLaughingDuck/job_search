from queries import get_jobs
import sqlite3
import webbrowser






def apply():
    '''
    Go through the available job listings. Each one is presented to the user,
    and the url is opened in a browser.
    '''
    conn = sqlite3.connect("job_search_database.sqlite", isolation_level=None)
    listings = conn.execute("SELECT id, job_title, company, url FROM jobs WHERE accepting_applications = 1 AND i_have_applied = 0;").fetchall()
    
    if len(listings) == 0:
        print("\nThere are currently no saved job listings for you to apply to.")
        return None
    else: pass

    for job in listings:
        # Present the job listing
        print("\nHere is a job:")
        print(f"Title: {job[1]}")
        print(f"Company: {job[2]}")

        # Open job listing url
        webbrowser.open(job[3], new=2)

        # Prompt the user to give a relevance score
        print("\nPlease give a relevance score:")
        print("\t\"3\": Exactly what I'm looking for!")
        print("\t\"2\": Kind of what I'm looking for.")
        print("\t\"1\": If there is nothing else available.")
        print("\t\"0\": Completely irrelevant to me.")
        print("\t\"null\": Set to null")
        inp = input(">")

        if inp in ["3", "2", "1", "0"]: conn.execute(f"UPDATE jobs SET relevance_score = {int(inp)} WHERE id = {job[0]}")
        elif inp == "null": print("Leaving the relevance score untouched.")
        else: print("Unknown relevance score. Proceeding without altering.")

        # Prompt the user for action
        print("\nPlease specify a desired action:")
        print("\t\"next\": View the next job listing.")
        print("\t\"applied\": Make a note that you applied to this position.")
        print("\t\"closed\": Make a note that this job listing has already been closed.")
        inp = input(">")

        if inp == "next": continue
        elif inp == "applied": conn.execute(f"UPDATE jobs SET i_have_applied = 1 WHERE id = {job[0]}")
        elif inp == "closed": conn.execute(f"UPDATE jobs SET accepting_applications = 0 WHERE id = {job[0]}")
        else: print("Unknown command. Proceeding without altering.")

        print("--------------------------------------------")


def help_message():
    '''
    Show the available commands.
    '''
    print("\nThese are the available commands:")
    print("\tapply: Go through the available job listings in the database.")
    print("\tend: End program.")
    print("\thelp: Show this message.")


# THE UI LOOP
print("\nThis is the UI for interacting with my jobs DB.")

print("\nQuerying 'TheirStack' for job listings...")
get_jobs(masked_data=False)

while True:
    print("\nPlease select an option.")
    inp = input(">")
    #inp = "apply"

    if inp == "apply": apply()

    if inp == "end": break

    if inp == "help": help_message()
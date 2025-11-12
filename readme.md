# Looking for jobs?
Manage and organize your job applications in this simple desktop app! You can manually add, edit and delete applications, change status ("applied", "rejected"), store personal comments, filter on status, sort, and search. You can also retrieve relevant applications automatically via an API.

# Background
I created this system when I was in the process of applying for jobs, and daily had to wade through loads of job listings, and keep track of my ongoing processes. At first I used a combination of notebooks and spreadsheets, but I wanted a more organized and reliable system, so I decided to streamline my process. The system now consists of a Graphical User Interface in the form of an app written in Python with tkinter, as well as a local SQLite database to store your applications, and is integrated with [theirstack.com](https://theirstack.com), who supply an API for retrieving online job listings. Your specific requirements such as job titles, location and seniority can be specified within the app. This functionality requires you to sign up for a free TheirStack account. The free tier is currently limited up to 200 jobs per month.

# How to use (Version 1.8.2)
1) Open the latest release in the menu to the right, and download 'app.exe'. Put it in a dedicated local folder, like 'job_application_program_folder/'. The program will automatically save additional program files ('db.sqlite', 'LOG.log', 'keys.json') to this folder.
2) Run 'app.exe'.
3) To set up automatic retrieval of job applications:
    - Create a [theirstack.com](https://theirstack.com) account.
    - Grab the API key, and insert it in the corresponding text box after clicking on **Settings** in the app. Click **Save**.
    - Now you can retrieve job listings automatically by clicking **Find job listings**. The number of used tokens is shown within the app, and resets monthly.

# Editing
The app comes with buttons to
- `Add job` (Manually add a job to the database, for example a job listing you found yourself)
- `Edit job` (Edit data associated with a specific job listing)
- `Show Description` (Show the posted description of a specific job listing. Good for manually evaluating if a job is relevant.)
- `Delete job` (Deletes one job that is selected)

# Retrieve new job listings
The app comes with built-in functionality for retrieving jobs from an online API. To set this up, follow the instructions under "How to use" above. Within the app, the following buttons and information are available.
- `Settings` (Click to enter your API token, and edit your job preferences. Click `Save settings` when you are finished.)
    - `Max number of jobs` (Every time you click `Find job listings` at the home screen, up to this many jobs are retrieved. Keep it low to avoid accidentally using up your API tokens.)
    - `Job titles` (Job titles that are relevant to you. Separate multiple with a comma and no space. For example 'Engineer,Environmental Engineer,Chemist')
    - `Job titles` (Job titles and/or seniority to *exclude*, mostly this can be ignored, but it can be useful to put 'Senior' here if you are only interested in junior and mid level roles)
    - `Location` (Search for locations, and select and toggle the relevant ones. You can do this multiple times, to build up a query for jobs in both Stockholm and Berlin at the same time for example.)
- `Find job listings` (Send a request for jobs to the API. If masking is disabled, this will consume one token for every job.)
- `Mask data` (Whether or not to mask data. If enabled, important job information is hidden (like company name and URL), but API tokens are not consumed. This is useful if you want to fine-tune your query settings without using up API tokens.)

# Filtering
The app provides two kinds of filtering on your jobs:
- `Filter` (Put in a search term, click `Apply`, and the program will filter on jobs where the *company name* or *job title* matches.)
- `Filter on status` (Select a filter on the job status. This allows you to show only jobs that you have applied to, or got rejected from, or that you haven't applied to yet.)

# Bugs? Errors?
Please report any bugs, or other strange behaviours by creating an issue! Describe the problem as thoroughly as possible, and consider posting part of the 'LOG.log' file with your description.
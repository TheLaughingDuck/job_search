# Looking for jobs?
Manage and organize your job applications in this simple desktop app! You can manually add, edit and delete applications, change status ("applied", "rejected"), store personal comments, filter on status, sort, and search. You can also retrieve relevant applications automatically via an API.

# Background
I created this system when I was in the process of applying for jobs, and daily had to wade through loads of job listings, and keep track of my ongoing processes. At first I used a combination of notebooks and spreadsheets, but I wanted a more organized and reliable system, so I decided to streamline my process. The system now consists of a Graphical User Interface in the form of an app written in Python with tkinter, as well as a local SQLite database to store your applications, and is integrated with [TheirStack.com](TheirStack.com), who supply an API for retrieving online job listings. Your specific requirements such as job titles, location and seniority can be specified within the app. This functionality requires you to sign up for a free TheirStack account. The free tier is currently limited up to 200 jobs per month.

# How to use (Version 1.8.2)
1) Open the latest release in the menu to the right, and download 'app.exe'. Put it in a dedicated local folder, like 'job_application_program_folder/'. The program will automatically save additional program files ('db.sqlite', 'LOG.log', 'keys.json') to this folder.
2) Run 'app.exe'.
3) To set up automatic retrieval of job applications:
    - Create a [TheirStack.com](TheirStack.com) account.
    - Grab the API key, and insert it in the corresponding text box after clicking on **Settings** in the app. Click **Save**.
    - Now you can retrieve job listings automatically by clicking **Find job listings**. The number of used tokens is shown within the app, and resets monthly.

# Bugs? Errors?
Please report any bugs, or other strange behaviours by creating an issue! Describe the problem as thoroughly as possible, and consider posting part of the 'LOG.log' file with your description.
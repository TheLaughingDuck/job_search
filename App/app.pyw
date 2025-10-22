import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from queries import get_jobs, get_token_usage
from utils import run_sql, build_db, json_get_key, json_set_key, create_keys_file
import uuid

import logging
logging.basicConfig(filename="LOG.log",
                    filemode="a",
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
logging.info("Started App")


class JobAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Applications Manager")

        # Create database and connect
        build_db(db="db.sqlite")
        self.conn = sqlite3.connect("db.sqlite")

        # Create keys file (if it doesn't already exist)
        create_keys_file()

        # Environment variables
        self.retrieved_jobs = 0
        self.job_query = ""

        # --- Button events ---
        self.root.bind("<Return>", self.enter_key_pressed)
        
        # --- Top Buttons ---
        top_frame = tk.Frame(root)
        top_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(top_frame, text="Add Job", command=self.add_job).pack(side="left", padx=5)
        tk.Button(top_frame, text="Edit Job", command=self.edit_job).pack(side="left", padx=5)
        tk.Button(top_frame, text="Show Description", command=self.show_description).pack(side="left", padx=5)
        tk.Button(top_frame, text="Delete Job", command=self.delete_job).pack(side="left", padx=5)
        tk.Button(top_frame, text="Settings", command=self.settings_window).pack(side="left", padx=5)

        # --- Filter / Sort ---
        filter_frame = tk.Frame(root)
        filter_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(filter_frame, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        tk.Entry(filter_frame, textvariable=self.filter_var).pack(side="left", padx=5)
        tk.Button(filter_frame, text="Apply", command=self.refresh_jobs).pack(side="left", padx=5)
        
        self.filter_setting = tk.StringVar()
        self.filter_setting.set("Show all")
        filter_options = ['Show all', 'Show live applications', 'Show applicable', 'Show rejected']
        tk.OptionMenu(filter_frame, self.filter_setting, *filter_options, command=lambda _: self.refresh_jobs()).pack(side="left", padx=5)
        #tk.Button(filter_frame, text="Toggle Living Applications", command=self.show_live_applications).pack(side="left", padx=5)
        #tk.Button(filter_frame, text="Toggle Applicable", command=self.toggle_applicable).pack(side="left", padx=5)
        self.retrieved_jobs_label = tk.Label(filter_frame, text="---", borderwidth=1, relief="groove")
        self.retrieved_jobs_label.pack(side="left", padx=20)

        # API Request button
        tk.Button(filter_frame, text="Find job listings", command=self.find_jobs).pack(side="left", padx=10)

        # Show API token usage
        self.api_token_label = tk.Label(filter_frame, text="---", borderwidth=1, relief="groove")
        self.api_token_label.pack(side="left", padx=5)

        # --- Job List (Treeview) ---
        self.tree = ttk.Treeview(root, columns=("jobtitle", "company", "location", "dateposted", "status", "comment"), show="headings")
        self.tree.heading("jobtitle", text="Title", command=lambda: self.refresh_jobs("job_title"))
        self.tree.heading("company", text="Company", command=lambda: self.refresh_jobs("company"))
        self.tree.heading("location", text="Location", command=lambda: self.refresh_jobs("location"))
        self.tree.heading("dateposted", text="Date posted", command=lambda: self.refresh_jobs("date_posted"))
        #self.tree.heading("description", text="Description", command=lambda: self.sort_by("description"))
        self.tree.heading("status", text="Status", command=lambda: self.refresh_jobs("status"))
        self.tree.heading("comment", text="Comment", command=lambda: self.refresh_jobs("comment"))
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Refresh the list of jobs (from the local database)
        self.refresh_jobs()

    def refresh_jobs(self, sort_by=None):
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Set up start of query
        self.job_query = "SELECT id, job_title, company, location, date_posted, status, comment FROM jobs"

        # Create variables to collect search parameters, and assemble the where query
        params = []
        where_query = []

        # Check whether any user-specified filter applies
        if self.filter_setting.get() != "Show all" or self.filter_var.get():
            self.job_query += " WHERE "

            # Adjust SQL query with relevant text FILTER
            if self.filter_var.get():
                where_query.append("(company LIKE ? OR job_title LIKE ?)")
                like = f"%{self.filter_var.get()}%"
                params.extend([like, like])

        # Adjust SQL query with relevant status FILTER
        if self.filter_setting.get() == "Show all": pass
        elif self.filter_setting.get() == "Show live applications": where_query.append("status = 'Applied'")
        elif self.filter_setting.get() == "Show applicable": where_query.append("status = '---'")
        elif self.filter_setting.get() == "Show rejected": where_query.append("status = 'Rejected'")

        self.job_query += " AND ".join(where_query)

        # Adjust SQL query with relevant ordering
        if sort_by:
            self.job_query += f" ORDER BY {sort_by}"
        
        # Start cursor
        c = self.conn.cursor()
        
        # Perform query and insert the results in the UI table
        #print(f"The job query is:\n\t{self.job_query}")
        for row in c.execute(self.job_query, params):
            self.tree.insert("", "end", iid=row[0], values=row[1:])
        
        # Update label with the number of shown jobs
        self.retrieved_jobs = len(self.tree.get_children())
        self.retrieved_jobs_label.configure(text="Showing {n_jobs} jobs".format(n_jobs=self.retrieved_jobs))
        self.retrieved_jobs_label.update()

        # Update the label that shows how many tokens have been used
        # No immediate need to this when just updating the shown list. Remove.
        #self.update_token_usage_label()
    
    def enter_key_pressed(self, event):
        '''Refresh the UI table when 'Return' is pressed.'''
        #print(event.char, event.keysym, event.keycode)
        self.refresh_jobs()


    ###### V ###### TOP BUTTONS ###### V ######

    def add_job(self):
        self.edit_window(job_id=False)

    def edit_job(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Select Job", "Please select a job to edit.")
            return
        self.edit_window(job_id=selected)
    
    def show_description(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Select Job", "Please select a job.")
            return
        self.description_window(job_id=selected)
    
    def delete_job(self):
        job_id = self.tree.focus()
        if not job_id:
            messagebox.showwarning("Select Job", "Please select a job to delete.")
            return
        
        # Prompt the user to confirm delete
        response = messagebox.askyesno(title="Delete job", message="You are about to delete this job, are you sure?")
        if response:
            c = self.conn.cursor()
            c.execute(f"DELETE FROM jobs WHERE id='{job_id}';")
            self.conn.commit()
            
            self.refresh_jobs()
        else: return

    
    def find_jobs(self):
        '''Request jobs from TheirStack and update app.'''
        get_jobs(masked_data=False)
        self.refresh_jobs()

        # Check current token usage
        usage = self.update_token_usage_label()
        try:
            if (usage[0] != "-") and (usage[0] >= usage[1]):
                logging.info("Attempted job request, but user is out of API tokens.")
                messagebox.showinfo(title="Error", message="You can't request more jobs, because you are out of API tokens this month.")
        except Exception as e:
            logging.warning(f"Unexpected error: {e}")
            messagebox.showwarning(title="Error", message=e)


    ###### ^ ###### TOP BUTTONS ###### ^ ######


    def edit_window(self, job_id):
        win = tk.Toplevel(self.root)
        win.title("Edit Job" if job_id else "Add Job")

        jobtitle_var = tk.StringVar()
        company_var = tk.StringVar()
        url_var = tk.StringVar()
        dateposted_var = tk.StringVar()
        location_var = tk.StringVar()
        remote_var = tk.BooleanVar()
        hybrid_var = tk.BooleanVar()
        salarystring_var = tk.StringVar()
        seniority_var = tk.StringVar()
        relevance_var = tk.StringVar()
        comment_var = tk.StringVar()
        status_var = tk.StringVar()

        if job_id:
            c = self.conn.cursor()
            c.execute("SELECT job_title, company, url, date_posted, location, remote, hybrid, salary_string, seniority, relevance, comment, status FROM jobs WHERE id=?", (job_id,))
            jobtitle, company, url, dateposted, location, remote, hybrid, salarystring, seniority, relevance, comment, status = c.fetchone()
            jobtitle_var.set(jobtitle)
            company_var.set(company)
            url_var.set(url)
            dateposted_var.set(dateposted)
            location_var.set(location)
            remote_var.set(remote)
            hybrid_var.set(hybrid)
            salarystring_var.set(salarystring)
            seniority_var.set(seniority)
            relevance_var.set(relevance)
            comment_var.set(comment)
            status_var.set(status)
        else:
            status_var.set('---')

        ######## Labels and entryboxes
        tk.Label(win, text="Job title").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=jobtitle_var, width=40).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(win, text="Company").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=company_var, width=40).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(win, text="URL").grid(row=2, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=url_var, width=40).grid(row=2, column=1, padx=5, pady=5)

        tk.Label(win, text="Date posted").grid(row=3, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=dateposted_var, width=40).grid(row=3, column=1, padx=5, pady=5)

        tk.Label(win, text="Location").grid(row=4, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=location_var, width=40).grid(row=4, column=1, padx=5, pady=5)

        tk.Checkbutton(win, text="Remote", variable=remote_var, onvalue=1, offvalue=0).grid(row=5, column=1)

        tk.Checkbutton(win, text="Hybrid", variable=hybrid_var, onvalue=1, offvalue=0).grid(row=6, column=1)

        tk.Label(win, text="Salary").grid(row=7, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=salarystring_var, width=40).grid(row=7, column=1, padx=5, pady=5)

        tk.Label(win, text="Seniority").grid(row=8, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=seniority_var, width=40).grid(row=8, column=1, padx=5, pady=5)

        tk.Label(win, text="Relevance").grid(row=9, column=0, padx=5, pady=5)
        relevance_menu = tk.OptionMenu(win, relevance_var, '---', 'Perfect', 'Relevant', 'Vaguely relevant', 'Irrelevant')
        relevance_menu.grid(row=9, column=1, padx=5, pady=5)

        tk.Label(win, text="Status").grid(row=10, column=0, padx=5, pady=5)
        status_menu = tk.OptionMenu(win, status_var, '---', 'Applied', 'Rejected', 'I lack requirements', 'Closed')
        status_menu.grid(row=10, column=1, padx=5, pady=5)        

        tk.Label(win, text="Your personal comments").grid(row=11, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=comment_var, width=40).grid(row=11, column=1, padx=5, pady=5)

        def save(job_id=job_id):
            c = self.conn.cursor()
            if job_id:
                c.execute("UPDATE jobs SET job_title=?, company=?, url=?, date_posted=?, location=?, remote=?, hybrid=?, salary_string=?, seniority=?, relevance=?, comment=?, status=? WHERE id=?",
                          (jobtitle_var.get(), company_var.get(), url_var.get(), dateposted_var.get(), location_var.get(), remote_var.get(), hybrid_var.get(), salarystring_var.get(), seniority_var.get(), relevance_var.get(), comment_var.get(), status_var.get(), job_id))
            else:
                job_id = uuid.uuid4().__str__()
                c.execute("INSERT INTO jobs (id, job_title, company, url, date_posted, location, remote, hybrid, salary_string, seniority, relevance, comment, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (job_id, jobtitle_var.get(), company_var.get(), url_var.get(), dateposted_var.get(), location_var.get(), remote_var.get(), hybrid_var.get(), salarystring_var.get(), seniority_var.get(), relevance_var.get(), comment_var.get(), status_var.get()))
            self.conn.commit()
            self.refresh_jobs()
            win.destroy()

        tk.Button(win, text="Save", font=("Courier", 20), width=10, command=save).grid(row=12, column=0, columnspan=2, pady=10)
    
    def settings_window(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")

        # TheirStack API token
        theirstack_token_var = tk.StringVar()
        theirstack_token_var.set(json_get_key("keys.json", "THEIRSTACK_TOKEN"))
        tk.Label(win, text="TheirStack API token\n(without any surrounding quotation marks)").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=theirstack_token_var, width=40).grid(row=0, column=1, padx=5, pady=5)

        # Jobs per request
        requestlimit_var = tk.IntVar()
        requestlimit_var.set(json_get_key("keys.json", "limit"))
        tk.Label(win, text="Max number of jobs per request\n(Keep low (5) to avoid using up API tokens quickly)").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=requestlimit_var, width=40).grid(row=1, column=1, padx=5, pady=5)

        # Relevant job titles
        job_title_or = tk.StringVar()
        job_title_or.set(",".join(json_get_key("keys.json", "job_title_or")))
        tk.Label(win, text="Job titles\n(separate multiple with commas, no space)").grid(row=2, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=job_title_or, width=40).grid(row=2, column=1, padx=5, pady=5)

        # Filter out jobs with
        job_title_not = tk.StringVar()
        job_title_not.set(",".join(json_get_key("keys.json", "job_title_not")))
        tk.Label(win, text="Exclude job titles or seniority\n(e.g. 'Senior', separate multiple with commas, no space)").grid(row=3, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=job_title_not, width=40).grid(row=3, column=1, padx=5, pady=5)

        # Location checkboxes
        locations = json_get_key("keys.json", "locations")
        loc_keys = list(locations.keys())
        loc_vars = {key: tk.IntVar(value=locations[key][0]) for key in loc_keys}
        tk.Label(win, text="Select locations you are interested in.").grid(row=4, column=0)
        for i, key in zip(range(0, len(loc_keys)), loc_keys):
            tk.Checkbutton(win, text=key, variable=loc_vars[key], onvalue=1, offvalue=0).grid(row=5+i, column=0)

        # Saving settings
        def save():
            try:
                json_set_key(fp="keys.json", key="THEIRSTACK_TOKEN", val=theirstack_token_var.get())
                json_set_key(fp="keys.json", key="job_title_or", val=job_title_or.get().split(","))
                json_set_key(fp="keys.json", key="job_title_not", val=job_title_not.get().split(","))
                json_set_key(fp="keys.json", key="limit", val=requestlimit_var.get())

                # Update locations in keys.json
                for key in loc_keys:
                    locations[key] = [loc_vars[key].get(), locations[key][1]]
                json_set_key(fp="keys.json", key="locations", val=locations)

                # Destroy the window
                win.destroy()
            except Exception as e:
                logging.info(e)
                messagebox.showerror(title="Error", message=e)

        tk.Button(win, text="Save", font=("Courier", 20), width=10, command=save).grid(row=30, column=0, columnspan=2, pady=10)



    # def error_window(self, message="..."):
    #     win = tk.Toplevel(self.root)
    #     win.title("ERROR")

    #     message = "An error occurred, outputting the following error message:\n\n" + str(message) + "\n\nSee the log file for further details."

    #     tk.Label(win, text=message).pack(side="top")
    #     tk.Button(win, text="OK", font=("Courier", 8), width=5, command=win.destroy).pack(side="bottom", pady=10)
    
    def update_token_usage_label(self):
        '''Updates the token usage label, and returns the number of used and total tokens'''
        usage = get_token_usage()
        self.api_token_label.configure(text="Used {} out of {} tokens".format(usage[0], usage[1]))
        self.api_token_label.update()

        return usage

        
    

    def description_window(self, job_id=None):
        '''
        Open a window showing the description of the selected job.
        This should speed up the main application.
        '''
        win = tk.Toplevel(self.root)
        win.title("Description")

        if job_id:
            c = self.conn.cursor()
            job_description = c.execute("SELECT description FROM jobs WHERE id=?", (job_id,)).fetchall()[0]

        text = tk.Text(win, wrap="word", width=50, height=15)
        text.insert("1.0", job_description)
        text.config(state="disabled")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        scroll = tk.Scrollbar(win, command=text.yview)
        text.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")




if __name__ == "__main__":
    root = tk.Tk()
    app = JobAppGUI(root)
    root.mainloop()

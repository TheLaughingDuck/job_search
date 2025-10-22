import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from queries import get_jobs
from utils import run_sql, build_db, json_get_key, json_set_key, create_keys_file

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
        tk.Button(top_frame, text="Settings", command=self.settings_window).pack(side="left", padx=5)
        #tk.Button(top_frame, text="Delete Job", command=self.delete_job).pack(side="left", padx=5)

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
        self.retrieved_jobs_label.pack(side="left", padx=50)

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

        # Query TheirStack for job listings
        get_jobs(masked_data=False)

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
    
    def enter_key_pressed(self, event):
        '''Refresh the UI table when 'Return' is pressed.'''
        #print(event.char, event.keysym, event.keycode)
        self.refresh_jobs()


    ###### V ###### TOP BUTTONS ###### V ######

    def add_job(self):
        self.edit_window()

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

    ###### ^ ###### TOP BUTTONS ###### ^ ######


    def edit_window(self, job_id=None):
        win = tk.Toplevel(self.root)
        win.title("Edit Job" if job_id else "Add Job")

        jobtitle_var = tk.StringVar()
        company_var = tk.StringVar()
        url_var = tk.StringVar()
        comment_var = tk.StringVar()
        status_var = tk.StringVar()

        if job_id:
            c = self.conn.cursor()
            c.execute("SELECT job_title, company, url, comment, status FROM jobs WHERE id=?", (job_id,))
            jobtitle, company, url, comment, status = c.fetchone()
            jobtitle_var.set(jobtitle)
            company_var.set(company)
            url_var.set(url)
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

        tk.Label(win, text="Status").grid(row=3, column=0, padx=5, pady=5)
        status_menu = tk.OptionMenu(win, status_var, '---', 'Applied', 'Rejected', 'I lack requirements', 'Closed')
        status_menu.grid(row=3, column=1, padx=5, pady=5)        

        tk.Label(win, text="comment").grid(row=4, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=comment_var, width=40).grid(row=4, column=1, padx=5, pady=5)

        def save():
            c = self.conn.cursor()
            if job_id:
                c.execute("UPDATE jobs SET job_title=?, company=?, url=?, comment=?, status=? WHERE id=?",
                          (jobtitle_var.get(), company_var.get(), url_var.get(), comment_var.get(), status_var.get(), job_id))
            else:
                c.execute("INSERT INTO jobs (id, job_title, company, url, comment, status) VALUES (?, ?, ?, ?, ?, ?)",
                          (job_id, jobtitle_var.get(), company_var.get(), url_var.get(), comment_var.get(), status_var.get()))
            self.conn.commit()
            self.refresh_jobs()
            win.destroy()

        tk.Button(win, text="Save", font=("Courier", 20), width=10, command=save).grid(row=5, column=0, columnspan=2, pady=10)
    
    def settings_window(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")

        # TheirStack API token
        theirstack_token_var = tk.StringVar()
        theirstack_token_var.set(json_get_key("keys.json", "THEIRSTACK_TOKEN"))
        tk.Label(win, text="TheirStack API token\n(without any surrounding quotation marks)").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(win, textvariable=theirstack_token_var, width=40).grid(row=0, column=1, padx=5, pady=5)

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

                # Update locations in keys.json
                for key in loc_keys:
                    locations[key] = [loc_vars[key].get(), locations[key][1]]
                json_set_key(fp="keys.json", key="locations", val=locations)

                # Destroy the window
                win.destroy()
            except Exception as e:
                logging.info(e)

        tk.Button(win, text="Save", font=("Courier", 20), width=10, command=save).grid(row=30, column=0, columnspan=2, pady=10)

    

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

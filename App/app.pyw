import tkinter as tk
from tkinter import ttk, messagebox, Scrollbar
import sqlite3
from queries import get_jobs, get_token_usage, get_locations
from utils import run_sql, build_db, json_get_key, json_set_key, create_keys_file
import uuid
import webbrowser

from style import HoverButton, HoverOptionMenu

from PIL import Image, ImageTk

import logging
logging.basicConfig(filename="LOG.log",
                    filemode="a",
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
logging.info("Started App")


class JobAppGUI:
    
    #####################################
    ###### V ###### SETUP ###### V ######
    #####################################

    def __init__(self, root):
        # --- Setup ---
        self.root = root
        self.root.title("Job Application Manager")

        build_db(db="db.sqlite")
        self.conn = sqlite3.connect("db.sqlite")
        
        create_keys_file()

        self.root.wm_iconphoto(False, ImageTk.PhotoImage(Image.open("DuckHead.png")))

        # --- Environment variables ---
        self.retrieved_jobs = 0
        self.job_query = ""
        self.mask_data = False # Masked requests do not consume API credits, which may be useful when experimenting with the query parameters.
        self.sort_column = ""
        self.sort_direction = "ASC" # This is used to invert the sort order if the user presses a column twice.


        # --- Keyboard button events ---
        self.root.bind("<Return>", self.enter_key_pressed)


        # --- Frames and Tree (used to organize the home page) ---
        toprow_frame = tk.Frame(root)
        toprow_frame.pack(fill="x", padx=10, pady=5)

        edit_frame = tk.Frame(toprow_frame, borderwidth=1,  relief="ridge")
        edit_frame.pack(side="left", padx=10, pady=5)

        query_frame = tk.Frame(toprow_frame, borderwidth=1, relief="ridge")
        query_frame.pack(side="left", padx=10, pady=5)

        bottomrow_frame = tk.Frame(root)
        bottomrow_frame.pack(fill="x", padx=10, pady=5)

        search_frame = tk.Frame(bottomrow_frame, borderwidth=1, relief="ridge")
        search_frame.pack(side="left", padx=10, pady=0)

        filterstatus_frame = tk.Frame(bottomrow_frame, borderwidth=1, relief="ridge")
        filterstatus_frame.pack(side="left", padx=10, pady=5)

        self.tree = ttk.Treeview(root, columns=("jobtitle", "company", "location", "dateposted", "status", "comment"), show="headings")
        scroll_bar = Scrollbar(root, width=20, command=self.tree.yview)
        scroll_bar.pack(side = "right", fill = "y")
        self.tree.config(yscrollcommand=scroll_bar.set)

        # --- Edit related buttons ---
        HoverButton(edit_frame, text="Add Job", command=self.add_job).pack(side="left", padx=5, pady=10)
        HoverButton(edit_frame, text="Edit Job", command=self.edit_job).pack(side="left", padx=5, pady=10)
        HoverButton(edit_frame, text="Show Description", command=self.show_description).pack(side="left", padx=5, pady=10)
        HoverButton(edit_frame, text="Delete Job", command=self.delete_job).pack(side="left", padx=5, pady=10)


        # --- Query buttons and information ---
        HoverButton(query_frame, text="Settings", command=self.settings_window).pack(side="left", padx=5, pady=10)
        HoverButton(query_frame, text="Find job listings", command=self.find_jobs).pack(side="left", padx=10)
        self.api_token_label = tk.Label(query_frame, text="---", borderwidth=1, relief="groove") # Show API token usage
        self.api_token_label.pack(side="left", padx=5)
        tk.Checkbutton(query_frame, text="Mask data (Important job details will be hidden,\nbut the query will not expend any API tokens.)", variable=self.mask_data, onvalue=1, offvalue=0, command=self.toggle_mask_setting).pack(side="left", padx=10)


        # --- Developer plug ---
        HoverButton(toprow_frame, text="This program was developed by \nSimon Jorstedt", command=self.creator, borderwidth=1, relief="groove").pack(side="right", padx=5)


        # --- Filter on search terms ---
        tk.Label(search_frame, text="Filter:").pack(side="left", pady=10)
        self.filter_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.filter_var).pack(side="left", padx=5)
        HoverButton(search_frame, text="Apply", command=self.refresh_jobs).pack(side="left", padx=5)
        

        # --- Filter on status  ---
        tk.Label(filterstatus_frame, text="Filter on status:").pack(side="left", padx=(0,0), pady=10)
        
        self.filter_setting = tk.StringVar()
        self.filter_setting.set("Show all")
        filter_options = ['Show all', 'Show live applications', 'Show applicable', 'Show rejected']
        HoverOptionMenu(filterstatus_frame, self.filter_setting, command=lambda _: self.refresh_jobs(), *filter_options).pack(side="left", padx=5)
        self.retrieved_jobs_label = tk.Label(bottomrow_frame, text="---", borderwidth=1, relief="groove", padx=2)
        self.retrieved_jobs_label.pack(side="left", padx=20)


        # --- Job List (Treeview) ---
        self.tree.heading("jobtitle", text="Title", command=lambda: self.refresh_jobs("job_title"))
        self.tree.heading("company", text="Company", command=lambda: self.refresh_jobs("company"))
        self.tree.heading("location", text="Location", command=lambda: self.refresh_jobs("location"))
        self.tree.heading("dateposted", text="Date posted", command=lambda: self.refresh_jobs("date_posted"))
        self.tree.heading("status", text="Status", command=lambda: self.refresh_jobs("status"))
        self.tree.heading("comment", text="Comment", command=lambda: self.refresh_jobs("comment"))
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Retrieve saved column widths
        column_widths = {name: width for name, width in zip(self.tree["columns"], json_get_key("keys.json", "treeview_column_widths"))}
        
        # Set column widths
        self.tree.column("jobtitle", width=column_widths["jobtitle"])
        self.tree.column("company", width=column_widths["company"])
        self.tree.column("location", width=column_widths["location"])
        self.tree.column("dateposted", width=column_widths["dateposted"])
        self.tree.column("status", width=column_widths["status"])
        self.tree.column("comment", width=column_widths["comment"])

        # Button to save current column widths
        HoverButton(bottomrow_frame, text="Save column widths", command=self.save_column_widths).pack(side="right")

        # Refresh the list of jobs (from the local database)
        self.refresh_jobs()

    #####################################
    ###### ^ ###### SETUP ###### ^ ######
    #####################################








    ###########################################
    ###### V ###### TOP BUTTONS ###### V ######
    ###########################################

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
            messagebox.showwarning("Select Job", "Please select a job to show its Description.")
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
    
    def creator(self):
        webbrowser.open("https://github.com/TheLaughingDuck/job_search")
    
    def find_jobs(self):
        '''Request jobs from TheirStack and update app.'''
        get_jobs(masked_data=self.mask_data)
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
    
    def toggle_mask_setting(self):
        self.mask_data = False if self.mask_data else True
        #print("Mask setting is", self.mask_data)


    ###########################################
    ###### ^ ###### TOP BUTTONS ###### ^ ######
    ###########################################








    ###########################################
    ###### V ###### SUB WINDOWS ###### V ######
    ###########################################

    #### EDIT/ADD WINDOW
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
            remote_var.set("FALSE" if remote is None else remote) # In case remote and hybrid are NULL by default when manually adding a job.
            hybrid_var.set("FALSE" if hybrid is None else hybrid) # This was the case in releases up to v1.11.3 (In newer versions FALSE is the specified default when the database is created).
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
        relevance_menu = HoverOptionMenu(win, relevance_var, '---', 'Perfect', 'Relevant', 'Vaguely relevant', 'Irrelevant')
        relevance_menu.grid(row=9, column=1, padx=5, pady=5)

        tk.Label(win, text="Status").grid(row=10, column=0, padx=5, pady=5)
        status_menu = HoverOptionMenu(win, status_var, '---', 'Applied', 'Rejected', 'I lack requirements', 'Closed')
        status_menu.grid(row=10, column=1, padx=5, pady=5)        

        tk.Label(win, text="Your personal comments").grid(row=11, column=0, padx=5, pady=5)
        #tk.Entry(win, textvariable=comment_var, width=40).grid(row=11, column=1, padx=5, pady=5)
        comment_box = tk.Text(win, wrap="word", width=50, height=5)
        comment_box.insert("1.0", comment_var.get())
        comment_box.grid(row=11, column=1, padx=5, pady=5)
        comment_var.set(comment_box.get("1.0", "end-1c"))

        def save(job_id=job_id):
            # Set the comment variable from the comment box
            comment_var.set(comment_box.get("1.0", "end-1c"))
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

        HoverButton(win, text="Save", font=("Courier", 20), width=10, command=save).grid(row=12, column=0, columnspan=2, pady=10)
    

    #### SETTINGS WINDOW
    def settings_window(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")

        top_frame = tk.Frame(win)
        top_frame.pack(fill="x", padx=10, pady=5)
        #tk.Label(top_frame, text="Configure Query Settings", font=("Courier", 20)).pack(side="top", padx=5)

        # TheirStack API token
        theirstack_token_var = tk.StringVar()
        theirstack_token_var.set(json_get_key("keys.json", "THEIRSTACK_TOKEN"))
        tk.Label(top_frame, text="TheirStack API token\n(without any surrounding quotation marks)").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(top_frame, textvariable=theirstack_token_var, width=40).grid(row=0, column=1, padx=5, pady=5)

        # Jobs per request
        requestlimit_var = tk.IntVar()
        requestlimit_var.set(json_get_key("keys.json", "limit"))
        tk.Label(top_frame, text="Max number of jobs per request\n(Keep low (5) to avoid using up API tokens quickly)").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(top_frame, textvariable=requestlimit_var, width=40).grid(row=1, column=1, padx=5, pady=5)

        # Relevant job titles
        job_title_or = tk.StringVar()
        job_title_or.set(",".join(json_get_key("keys.json", "job_title_or")))
        tk.Label(top_frame, text="Job titles\n(separate multiple with commas, no space)").grid(row=2, column=0, padx=5, pady=5)
        tk.Entry(top_frame, textvariable=job_title_or, width=40).grid(row=2, column=1, padx=5, pady=5)

        # Filter out jobs with
        job_title_not = tk.StringVar()
        job_title_not.set(",".join(json_get_key("keys.json", "job_title_not")))
        tk.Label(top_frame, text="Exclude job titles or seniority\n(e.g. 'Senior', separate multiple with commas, no space)").grid(row=3, column=0, padx=5, pady=5)
        tk.Entry(top_frame, textvariable=job_title_not, width=40).grid(row=3, column=1, padx=5, pady=5)
        
        bottom_frame = tk.Frame(win)
        bottom_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(bottom_frame, text="Configure Location", font=("Courier", 20)).pack(side="top", padx=5)
        
        tk.Label(bottom_frame, text="Filter:").pack(side="left", padx=5)
        self.location_filter_var = tk.StringVar()
        tk.Entry(bottom_frame, textvariable=self.location_filter_var).pack(side="left", padx=5)
        HoverButton(bottom_frame, text="Search", command=self.refresh_locations).pack(side="left", padx=5)
        HoverButton(bottom_frame, text="Toggle", command=self.update_location_selection).pack(side="left", padx=5)
        
        self.tree_locs = ttk.Treeview(win, columns=("name", "country", "is_selected"), show="headings")
        self.tree_locs.heading("name", text="Name", command=lambda: self.refresh_jobs("job_title"))
        self.tree_locs.heading("country", text="Country", command=lambda: self.refresh_jobs("job_title"))
        self.tree_locs.heading("is_selected", text="Selected", command=lambda: self.refresh_jobs("job_title"))
        self.tree_locs.pack(padx=5)

        # Retrieve and show the currently saved locations
        self.locations = [] # Instantiate the locations as empty (and then load the saved ones from keys.json in self.refresh_locations()).
        self.refresh_locations(search=False)

        # Saving settings
        def save():
            try:
                json_set_key(fp="keys.json", key="THEIRSTACK_TOKEN", val=theirstack_token_var.get())
                json_set_key(fp="keys.json", key="job_title_or", val=job_title_or.get().split(","))
                json_set_key(fp="keys.json", key="job_title_not", val=job_title_not.get().split(","))
                json_set_key(fp="keys.json", key="limit", val=requestlimit_var.get())
                json_set_key(fp="keys.json", key="locations_v2", val=[dic for dic in self.locations if dic['selected'] == "Yes"])

                # Destroy the window
                win.destroy()
            except Exception as e:
                logging.info(e)
                messagebox.showerror(title="Error", message=e)

        HoverButton(bottom_frame, text="Save settings", font=("Courier", 20), width=20, command=save).pack(side="bottom", pady=10)#.grid(row=30, column=0, columnspan=2, pady=10)


    #### DESCRIPTION WINDOW
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
        text.pack(side="left", fill="y")
        text.insert("1.0", job_description)
        text.config(state="disabled")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        scroll = tk.Scrollbar(win, command=text.yview)
        text.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
    
    ###########################################
    ###### ^ ###### SUB WINDOWS ###### ^ ######
    ###########################################
    







    ##################################################
    ###### V ###### INTERNAL FUNCTIONS ###### V ######
    ##################################################

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
            # Change the sort direction if the same column is clicked twice
            if self.sort_column == sort_by:
                self.sort_direction = "ASC" if self.sort_direction == "DESC" else "DESC"
            
            # Set the new column to sort
            self.sort_column = sort_by
            
            self.job_query += f" ORDER BY {sort_by} {self.sort_direction}"
        
        # Start cursor
        c = self.conn.cursor()
        
        # Perform query and insert the results in the UI table
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


    def update_token_usage_label(self):
        '''Updates the token usage label, and returns the number of used and total tokens'''
        usage = get_token_usage()
        self.api_token_label.configure(text="Used {} out of {} tokens".format(usage[0], usage[1]))
        self.api_token_label.update()

        return usage
    

    def update_location_selection(self):
        '''
        Toggle the selection status of the selected jobs when user presses the toggle button.
        '''

        #print("\nself.locations prior to update:\n\t", "\n\t".join([i["name"]+"     "+i["selected"] for i in self.locations]))
        for element in self.locations:
            # Check if this location element is among the selected
            if element['id'] in [int(i) for i in self.tree_locs.selection()]:

                # Toggle the "selected" value, and update the tree
                element['selected'] = "Yes" if element['selected'] == "No" else "No"
                self.tree_locs.item(element['id'], values=(element['name'], element['country_name'], element['selected']))
        
        #print("\nself.locations after update:\n\t", "\n\t".join([i["name"]+"     "+i["selected"] for i in self.locations]))
    

    def refresh_locations(self, search=True):
        '''
        Search for locatons related to the search_term.

        Whether to search is toggle-able, so that the already saved locations can be shown without
        having to make a new empty search every time the settings window opens.
        '''
        # Clear unselected locations from the current tree
        # Remove all instead. The ones with "Yes" should still be in self.locations
        for id in self.tree_locs.get_children(): self.tree_locs.delete(id)
        # for id in self.tree_locs.get_children():
        #     if self.tree_locs.item(id)["values"][2] == "No": self.tree_locs.delete(id)
        
        # Also clear the locations that are *not* selected
        self.locations = list(filter(lambda x: x["selected"] == "Yes", self.locations))
        
        # Retrieve new locations based on the search term
        if search:
            #print("\n\nSEARCHING FOR NEW LOCATIONS\n\n")
            searched_locations = get_locations(search_term=self.location_filter_var.get())
        else: searched_locations = []

        # Retrieve previously saved locations from keys.json
        saved_locations = json_get_key("keys.json", "locations_v2")
        
        # Iterate through the saved and searched locations, and append the ones that
        # are not already in self.locations (the "working memory" while the app is running)
        for element in saved_locations + searched_locations:
            #print(self.locations)
            if element['id'] not in [elem['id'] for elem in self.locations]:
                element['selected'] = element['selected'] #'No'
                self.locations += [{'id': element['id'], 'name': element['name'], 'country_name': element['country_name'], 'selected': element['selected']}] #[element]  

        #shown_locations = get_locations(search_term=self.location_filter_var.get())
        #shown_locations = [{'id': 123, "name":"A", "country_name": "ASD"}, {'id': 456, "name":"B", "country_name": "BNM"}]
        #print(f"\nAll of it: {self.locations}")

        # Insert the relevant locations into the tree
        for row in self.locations:
            self.tree_locs.insert("", "end", iid=row['id'], values=[row['name'], row['country_name'], row['selected']])
    

    def save_column_widths(self):
        # Save the column widths in the order in which the columns appear (left to right)
        json_set_key("keys.json", "treeview_column_widths", [self.tree.column(i)["width"] for i in list(self.tree["columns"])])

    ##################################################
    ###### ^ ###### INTERNAL FUNCTIONS ###### ^ ######
    ##################################################








if __name__ == "__main__":
    root = tk.Tk()
    app = JobAppGUI(root)
    root.mainloop()

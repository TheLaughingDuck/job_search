import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from queries import get_jobs

DB_FILE = "job_search_database.sqlite"

class JobAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Applications Manager")
        self.conn = sqlite3.connect(DB_FILE)
        #self.create_table()

        self.retrieved_jobs = 0
        self.job_query = ""
        
        # --- Top Buttons ---
        top_frame = tk.Frame(root)
        top_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(top_frame, text="Add Job", command=self.add_job).pack(side="left", padx=5)
        tk.Button(top_frame, text="Edit Job", command=self.edit_job).pack(side="left", padx=5)
        tk.Button(top_frame, text="Show Description", command=self.show_description).pack(side="left", padx=5)
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
        tk.OptionMenu(filter_frame, self.filter_setting, *filter_options, command=self.refresh_jobs).pack(side="left", padx=5)
        #tk.Button(filter_frame, text="Toggle Living Applications", command=self.show_live_applications).pack(side="left", padx=5)
        #tk.Button(filter_frame, text="Toggle Applicable", command=self.toggle_applicable).pack(side="left", padx=5)
        self.retrieved_jobs_label = tk.Label(filter_frame, text="---", borderwidth=1, relief="groove")
        self.retrieved_jobs_label.pack(side="left", padx=50)

        # --- Job List (Treeview) ---
        self.tree = ttk.Treeview(root, columns=("jobtitle", "company", "location", "dateposted", "status", "closed"), show="headings")
        self.tree.heading("jobtitle", text="Title", command=lambda: self.sort_by("jobtitle"))
        self.tree.heading("company", text="Company", command=lambda: self.sort_by("company"))
        self.tree.heading("location", text="Location", command=lambda: self.sort_by("location"))
        self.tree.heading("dateposted", text="Date posted", command=lambda: self.sort_by("dateposted"))
        #self.tree.heading("description", text="Description", command=lambda: self.sort_by("description"))
        self.tree.heading("status", text="Status", command=lambda: self.sort_by("status"))
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        print("\nQuerying 'TheirStack' for job listings...")
        get_jobs(masked_data=False)

        self.refresh_jobs()

    def refresh_jobs(self, sort_by=None):
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Update filter setting
        self.set_filter()

        c = self.conn.cursor()
        # self.job_query = "SELECT id, job_title, company, location, date_posted, status, closed FROM jobs"
        params = []

        # if self.filter_var.get():
        #     self.job_query += " WHERE"

        #     if self.hide_un_applicable: self.job_query += " closed != TRUE AND status IS NOT 'Applied'"
        #     if self.filter_var.get():
        #         self.job_query += " company LIKE ? OR job_title LIKE ?"
        #         like = f"%{self.filter_var.get()}%"
        #         params.extend([like, like, like])
        
        # Temporary solution
        #query = "SELECT id, job_title, company, location, date_posted, status, closed FROM jobs WHERE closed != TRUE AND status IS NULL"

        # if sort_by:
        #     self.job_query += f" ORDER BY {sort_by}"

        for row in c.execute(self.job_query, params):
            self.tree.insert("", "end", iid=row[0], values=row[1:])
        
        # Update label with the number of shown jobs
        self.retrieved_jobs = len(self.tree.get_children())
        self.retrieved_jobs_label.configure(text="Showing {n_jobs} jobs".format(n_jobs=self.retrieved_jobs))
        self.retrieved_jobs_label.update()


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

    def set_filter(self):
        self.job_query = "SELECT id, job_title, company, location, date_posted, status FROM jobs"

        if self.filter_setting.get() == "Show all": pass
        elif self.filter_setting.get() == "Show live applications": self.job_query += " WHERE status = 'Applied'"
        elif self.filter_setting.get() == "Show applicable": self.job_query += " WHERE status = '---'"
        elif self.filter_setting.get() == "Show rejected": self.job_query += " WHERE status = 'Rejected'"

        print(self.job_query)

    ###### ^ ###### TOP BUTTONS ###### ^ ######


    def edit_window(self, job_id=None):
        win = tk.Toplevel(self.root)
        win.title("Edit Job" if job_id else "Add Job")

        jobtitle_var = tk.StringVar()
        company_var = tk.StringVar()
        url_var = tk.StringVar()
        status_var = tk.StringVar()

        if job_id:
            c = self.conn.cursor()
            c.execute("SELECT job_title, company, url, status FROM jobs WHERE id=?", (job_id,))
            jobtitle, company, url, status = c.fetchone()
            jobtitle_var.set(jobtitle)
            company_var.set(company)
            url_var.set(url)
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

        def save():
            c = self.conn.cursor()
            if job_id:
                c.execute("UPDATE jobs SET job_title=?, company=?, url=?, status=? WHERE id=?",
                          (jobtitle_var.get(), company_var.get(), url_var.get(), status_var.get(), job_id))
            else:
                c.execute("INSERT INTO jobs (id, job_title, company, url, status) VALUES (?, ?, ?, ?, ?)",
                          (job_id, jobtitle_var.get(), company_var.get(), url_var.get(), status_var.get()))
            self.conn.commit()
            self.refresh_jobs()
            win.destroy()

        tk.Button(win, text="Save", font=("Courier", 20), width=10, command=save).grid(row=5, column=0, columnspan=2, pady=10)
    

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

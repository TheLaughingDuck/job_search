# Job Searching
Being in the process of applying for jobs, and having to wade through many applications, I decided to streamline my process. My system first queries the [TheirStack Job API](https://app.theirstack.com) for relevant jobs and saves the retrieved listings in a SQLite database. Then the jobs are processed, and I can go through them manually one by one, assigning a relevance score to each (see below), and marking the ones I apply to, and which are already closed.

## Relevance score
I plan to eventually create a model for sorting the jobs by relevance, to ensure each application is a good use of my time. First I need to collect a fair bit of data. I use the following classes:

- 0: "Completely irrelevant to me."
- 1: "If there is nothing else available."
- 2: "Kind of what I'm looking for."
- 3: "Exactly what I'm looking for!"
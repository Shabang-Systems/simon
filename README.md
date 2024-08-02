# #!/Simon
Hello! Welcome to Simon. Simon is a Python library that powers your entire semantic search stack: OCR, ingest, semantic search, extractive question answering, textual recommendation, and AI chat.

<div style="display: flex; align-items: center; width: 100%">
<img src="https://badge.fury.io/py/simon-search.svg"/>
</div>
<br />
<p align="center">
  <img src="https://i.imgur.com/lIn55Ck.png" />
</p>

Check out 🌐 [this online demo of the tool](https://wikisearch.shabang.io/) and browse 📖 [the full documentation](https://simon.shabang.io/start/)!

## 🏃 Quick Start
### Gather Your Tools
1. PostgresQL 15 with the Vector Plugin
    - A cloud service like [neon](https://simon.shabang.io/setup/Cloud-Databases/neon/), [supabase](https://simon.shabang.io/setup/Cloud-Databases/supabase/), [digital ocean](https://simon.shabang.io/setup/Cloud-Databases/digital-ocean/) is probably easiest
    - OR, you can also [self host the database following these instructions](https://simon.shabang.io/setup/detailed/#database-self-hosting)
2. [OpenAI API key](https://platform.openai.com/account/api-keys)
3. Python 3.9 or above. We recommend Python 3.11.
3. Optional: [Java](https://simon.shabang.io/setup/detailed/#java) if you want to use Simon's built in OCR tooling

### Install the Package
You can get the package from PyPi.

```bash
pip install simon-search -U
```

### Connect to Database

```python
import simon

# connect to your database
context = simon.create_context(
  "PROJECT_NAME",               # an arbitrary string id to silo your data.
                                # (store and search are per-project.)
  "sk-YOUR_OPENAI_API_KEY",     # must support GPT-4

  # postgres options. get these from your postgres provider.
  { "host": "your_db_host.com",
    "port": 5432,
    "user": "your_username",
    "password": "password", # or None
    "database": "your_database_name"
  }
)

# if needed, provision the database
simon.setup(context) # do this *only once once per new database*!!
```

The `project_name` is an arbitrary string you supply as the "folder"/"index" in the database where your data get stored. That is, the data ingested for one project cannot be searched in another.

You optionally can store the OpenAI key and Database info in an `.env` file or as Bash shell variables [following these instructions](https://simon.shabang.io/setup/detailed/#environment-variable-management).

### Storing Some Files

```python
ds = simon.Datastore(context)

# storing a remote webpage (or, if Java is installed, a PDF/PNG)
ds.store_remote("https://en.wikipedia.org/wiki/Chicken", title="Chickens")

# storing a local file (or, if Java is installed, a PDF/PNG)
ds.store_file("/Users/test/file.txt", title="Test File")

# storing some text
ds.store_text("Hello, this is the text I'm storing.", "Title of the Text", "{metadata: can go here}")
```

To learn more about ingestion, [head on over to the ingest overview page](https://simon.shabang.io/ingest/store/)!

<!-- We also have advanced ingestors and lower level APIs to bulk read lots of data; check out [the ingest recipes folder](https://github.com/Shabang-Systems/simon/tree/main/examples/ingest) for tutorials on how to store everything from S3 buckets to Google Drive files. -->

### Search Those Files
We all know why you came here: search! 

```python
s = simon.Search(context)

# Semantic Search
results = s.search("chicken habits")

# Recommendation (check out the demo: https://wikisearch.shabang.io/)
results = s.brainstorm("chickens are a species that") 

# LLM Answer and Extractive Question-Answering ("Quoting")
results = s.query("what are chickens?")
```

To learn more about search, including how to perform a boring keyword search or to stream your LLM output, [head on over to the search overview page](https://simon.shabang.io/search/search/)!

That's it! Simple as that. 

## 📖 Full Documentation
Check out the full documentation [available here](https://simon.shabang.io/) available here: from customizing your LLM, a REST API, and streaming your search results—we've got you covered.

## 🙌 Friends!
We are always looking for more friends to build together. If you are interested in learning more, getting enterprise support, or just want to chat, [visit this page](https://simon.shabang.io/about/). 

If you have a question about the package, please feel free to [post a discussion](https://github.com/Shabang-Systems/simon/discussions).

---

(C) 2024 Shabang Systems, LLC. Built with ❤️ and 🥗 in the SF Bay Area

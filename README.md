# #!/Simon
Hello! Welcome to Simon. Simon is a Python library that powers your entire semantic search stack: OCR, ingest, semantic search, extractive question answering, textual recommendation, and AI chat.

<div style="display: flex; align-items: center; width: 100%">
<img src="https://badge.fury.io/py/simon-search.svg"/>
</div>
<br /> 
<p align="center">
  <img src="https://i.imgur.com/lIn55Ck.png" />
</p>

Check out [this online demo of the tool!](https://wikisearch.shabang.io/)

## Quick Start
Are you ready to ~~rock~~ Simon? Let's do it.

First, [setup PostgreSQL with the Vector plugin with these instructions](https://github.com/Shabang-Systems/simon/wiki/Detailed-Setup-Guide#database-and-credentials). If you want to use Simon's built in OCR tooling, you will also need to [setup Java](https://github.com/Shabang-Systems/simon/wiki/Detailed-Setup-Guide#database-and-credentials).

After that, we can get started!

### Installation
You can get the package from PyPi.

```bash
pip install simon-search
```

### Context
All Simon operations require an object called the `AgentContext` to identify your database connection and credentials.

```python
import simon

context = simon.create_context("project_name", "sk-your_open_ai_api_key",
                               {"host": "your_db_host.com",
                                "port": 5432,
                                "user": "posgres",
                                "password": "super secure, or None",
                                "database": "dbname"})
```

The `project_name` is an arbitrary string you supply as the "folder"/"index" in the database where your data get stored. That is, the data ingested for one project cannot be searched in another.

You optionally can store the OpenAI key and Database info in an `.env` file or as Bash shell variables [following these instructions](https://github.com/Shabang-Systems/simon/wiki/Detailed-Setup-Guide#set-environment-variables) to streamline the setup.

### Provisioning
**Once per new database**, you have to provision the database; otherwise, no Simon operations will function.

```python
simon.setup(context)
```

### Storing Some Files
Simon is rather uninteresting as a search tool if you can't search things! To search things, though, you have to store some files into the database to search. The simplest way to ingest files is using:

```python
ds = simon.Datastore(context)

# storing a remote webpage (or, if Java is installed, a PDF/PNG)
ds.store("https://en.wikipedia.org/wiki/Chicken", title="Chickens")

# storing some text
ds.store_text("Hello, this is the text I'm storing.", "Title of the Text", "{metadata: can go here}")
```

We also have advanced ingestors and lower level APIs to bulk read lots of data; check out [the ingest recipes folder TODO TODO](./) for tutorials on how to store everything from local JSONs to Google Drive files.

### Search Those Files
We all know why you came here: search! 

```python
s = simon.Search(context)
```

**Semantic Search**

```python
results = s.search("chicken habits")
```

**Recommendation** ([check out the demo](https://wikisearch.shabang.io/))

```python
results = s.brainstorm("chickens are a species that") 
```

**LLM Answer and Extractive Question-Answering ("Quoting")**

```python
results = s.query("what are chickens?")
```

That's it! Simple as that. Want to learn more? Read the [full tutorial](https://github.com/Shabang-Systems/simon/blob/patch/error-handling/tutorial.py) to learn about the overall organization of the package; check out the [the recipes folder TODO TODO](./) for diving deep into Simon---speeding up your ingest, building a minimal REST-API, or fine tuning the LLM outputs: anything under the sun!

## Friends!
We are always looking for more friends to build together. If you are interested, please reach out by... CONTRIBUTING! Simply open a PR/Issue/Discussion, and we will be in touch.

<img src="https://mktdplp102wuda.azureedge.net/org-f4f78f7fa763412990f7f7ed79822b61/ba042d2e-95c0-ec11-983e-000d3a33908e/B2tXV68nr_6lraxPmSTeJsZ0O366bCH3mVOxHcDfKcY%21" width="20%"/>

---

(C) 2023 Shabang Systems, LLC. Built with ❤️ and 🥗 in the SF Bay Area

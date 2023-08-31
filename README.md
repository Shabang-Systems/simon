# #!/Simon
Hello! Welcome to Simon. Simon is an open-source pipeline which allows for the ingestion, storage, and processing of a large body of textual information with LLMs and a Postgres Database.

<p align="center">
  <img src="https://raw.githubusercontent.com/Shabang-Systems/simon/main/static/promo.png" />
</p>

Check out [this online demo of the tool!](https://wikisearch.shabang.io/)

This document serves as a very-minimal quickstart as we work to build this tool. Needless to say, this tool is alpha, at best. Proceed for your own risk and fun!
  
## Getting Started

Simon is a Python package to support semantic and LLM based search tasks. You interface with it like any other Python library; however, as it relies on an external database for storage services, we have some extra setup steps. 

### Database and Credentials
You will need to first setup an instance of Postgresql (**version 15**) on either a remote server or on your local machine. To set it up on your local machine, follow [the instructions available here](https://www.postgresql.org/download/). If setting up remotely, identify and follow the instructions of your cloud provider.

After setting up postgres, install the `vector` plugin [available here](https://github.com/pgvector/pgvector) (and already installed on most major cloud providers---just find instructions on how to enable it) to support Simon. 

You will also need OpenAI credentials. This will be available be either with the OpenAI public API, or Azure OpenAI Services.

Get the postgres connection credentials (for local installations, they are often `localhost:5432`, username `postgres` and no password; please refer to your distribution's instructions) and OpenAI credentials, and keep it for use in the steps below. 

### Java
If you would like to perform OCR or textual extraction from PDFs/impges with Simon, you optionally need Java installed/available to run `Tika` which is used for fetching/manipulating external data.

Check that it's available:

```
java -version
```

If not, install is system dependent. Quick fix for Ubuntu + Debian-based distros: `sudo apt install default-jre`. For macOS, run `brew install java` and be sure to follow the "Next Steps"/"Caveats" instructions afterwards.

### Install Simon!
You can install Simon from pypi.

```
pip install simon-search
```

all versions are figured with `Python 3.11`; all versions `>3.9` should be supported.

### Set Environment Variables
There are a few secret credentials (database, OpenAI) that we mentioned above. You can manually enter these credentials and configure OpenAI each time you use Simon using the `simon.create_context` function. However, we heavily recommend creating an `.env` file to store the credentials so you don't have type them in each time (or accidentally commit them :p).

To do this, create a `.env` file *in the directory* in which you plan to use Simon. Copy the `.env.example` [available at this link](https://github.com/Shabang-Systems/simon/blob/main/.env.example) and set values after the = sign.

If you don't want to create an `.env` file, you can also use the `export` directive in your bash shell to set all of the environment variables [listed in the file above for the current shell session](https://github.com/Shabang-Systems/simon/blob/main/.env.example).

Values set in your shell will override those in the `.env` file.

### Provision your Database

You need to manually seed the database schema when you're first setting up. To do this, fill out the environment variables found in `.env.example` [available at this link](https://github.com/Shabang-Systems/simon/blob/main/.env.example) into the `.env` file in any local directory, then run in the *same directory* in which you have your `.env` file:

```
simon-setup
```

to setup your database. If the program exits without error, you are good to go.

As with before, you can use the `export` directive in your bash shell or inline variable configuration to override or obviate the need to create an `.env` file:

### Run the code!

You are now ready to ~~rock~~ Simon! Follow the usage examples in `tutorial.py` [available here](https://github.com/Shabang-Systems/simon/blob/main/tutorial.py) get a full overview of the Python API.

Here's a quick start.

Assuming that you have an `.env` file located in the same directory as where you want to run these Python commands:

```python
### Import ###
import simon
context = simon.create_context("my-project-name")

### Ingest Some Files ###
db = simon.Datastore(context)
db.store("https://arxiv.org/pdf/1706.03762.pdf", "Attention is All you Need")

### Search for Things ###
s = simon.Search(context)
s.query("tell me about self attention") # llm query, extractive quotes, semantic search
s.brainstorm("self attention is a technology that:") # llm best-match resource identification, semantic search
s.search("self attention") # semantic search
```

<!-- This is not yet ready for prime time -->
<!-- ### REST API  -->

<!-- We also offer a fairly minimal API through `api.py`. To be able to do this, you need to first install the API server requirements: -->

<!-- ``` -->
<!-- pip install 'simon-search[web]' -->
<!-- ``` -->

<!-- then, run: -->

<!-- ``` -->
<!-- gunicorn simon.api:rest -w [num_workers] --timeout 1000 -->
<!-- ``` -->

<!-- No documentation quite yet, but we hope to get that up shortly. -->

## Friends!
We are always looking for more friends to build together. If you are interested, please reach out by... CONTRIBUTING! Simply open a PR/Issue/Discussion, and we will be in touch.

<img src="https://mktdplp102wuda.azureedge.net/org-f4f78f7fa763412990f7f7ed79822b61/ba042d2e-95c0-ec11-983e-000d3a33908e/B2tXV68nr_6lraxPmSTeJsZ0O366bCH3mVOxHcDfKcY%21" width="20%" />

---

(C) 2023 Shabang Systems, LLC. Built with ❤️ and 🥗 in the SF Bay Area

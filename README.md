# #!/Simon
Hello! Welcome to Simon. Simon is an open-source pipeline which allows for the ingestion, storage, and processing of a large body of textual information with LLMs. 

<p align="center">
  <img src="https://raw.githubusercontent.com/Shabang-Systems/simon/main/static/promo.png" />
</p>

Check out [this online demo of the tool!](https://wikisearch.shabang.io/)

This document serves as a very-minimal quickstart as we work to build this tool. Needless to say, this tool is alpha, at best. Proceed for your own risk and fun!
  
## Quickstart to run the code

### Postgresql
You need an psql instance running somewhere with the `vector` plugin [available here](https://github.com/pgvector/pgvector) (and installed on most major cloud providers) to support Simon. 

You will also need OpenAI credentials. This will be available be either with the OpenAI public API, or Azure OpenAI Services.

Get the postgres connection credentials and OpenAI credentials, and keep it for use in the steps below. 

### Requirements Setup
Begin by using the Python package management tool of your choice to install the requirements:

```
pip install -r requirements.txt
```

all versions are figured with `Python 3.11`; all versions `>3.9` should be supported.

### Set Environment Variables
Collect your credentials from the steps before, and create an `.env` file (copy `.env.example` and set values after the = sign) or through simple `export` directive in your bash shell.

An example of all the environment variables needed is in the `.env.example` file.

Values set in your shell will override those in the `.env` file.

### Provision your Database

You need to manually seed the database schema when you're first setting up. To do this, fill out the environment variables found in `.env.example` into the `.env` file in your local directory, then run:

```
python setup_database.py
```

To setup your database. If the program exits without error, you are good to go.

### Run the code!

You are now ready to ~~rock~~ Simon! Follow the usage examples in `tutorial.py` to get a full overview of the Python API.

## Misc notes

You'll need java installed/available to run `Tika` which is used for fetching/manipulating external data.

Check that it's available:

```
java -version
```

If not, install is system dependent.

(Quick fix for Ubuntu + Debian-based distros: `sudo apt install default-jre`)

## Friends!
We are always looking for more friends to build together. If you are interested, please reach out by... CONTRIBUTING! Simply open a PR/Issue/Discussion, and we will be in touch.

<img src="https://mktdplp102wuda.azureedge.net/org-f4f78f7fa763412990f7f7ed79822b61/ba042d2e-95c0-ec11-983e-000d3a33908e/B2tXV68nr_6lraxPmSTeJsZ0O366bCH3mVOxHcDfKcY%21" width="20%" />

---

(C) 2023 Shabang Systems, LLC. Built with ❤️ and 🥗 in the SF Bay Area

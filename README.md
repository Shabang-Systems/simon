# #!/Simon
Hello! Welcome to Simon. Simon is an open-source pipeline which allows for the ingestion, storage, and processing of a large body of textual information with LLMs. 

<p align="center">
  <img src="https://raw.githubusercontent.com/Shabang-Systems/simon/main/static/promo.png" />
</p>


We are working on demos of salient use cases soon, as well as a hosted instance of Simon. This document serves as a very-minimal quickstart as we work to build this tool. Needless to say, this tool is alpha, at best. Proceed for your own risk and fun!
  
## Quickstart to run the code

### Elastic
You need an ElasticSearch instance running somewhere to support Simon. One easy way to get it setup on your local machine is by [getting yourself a copy of Elastic here](https://www.elastic.co/downloads/elasticsearch) and following instructions there to get it running. There are also hosted options available online.

You will also need OpenAI credentials. This will be available be either with the OpenAI public API, or Azure OpenAI Services.

Get the Elastic connection credentials and OpenAI credentials, and keep it for the steps below. 

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

### Provision your Elastic

You need to manually seed the ElasticSearch schema when you're first setting up. To do this, create an ElasticSearch api instance, and use the following helper script once per **new elastic instance**:

```
python setup_es.py
```

If you find that you want to delete the existing ElasticSearch schema and start fresh, you can use the `--nuke` option:

```
python setup_es.py --nuke
```

### Run the code!

You are now ready to ~~rock~~ Simon! Follow the usage examples in `tutorial.py` to get a full overview of the Python API.

We also included an example for how a possible REST api can be structured in `rest.py`. This is not meant to be production ready (yet), but can be a good starting point for your own APIs. We hope to eventually support the REST use case in the future.

To serve a copy of the API, you can run:

```python
gunicorn -w 5 rest:simon_api -b [binding ip]:[binding port] --timeout 10000000 --preload
```

**don't use the above unless you are sure you can't use the Python API and roll your own REST solution**: the above is _not supported_ and just a demo use case.

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

We are proud to partner with Microsoft for Startups.

<img src="https://mktdplp102wuda.azureedge.net/org-f4f78f7fa763412990f7f7ed79822b61/ba042d2e-95c0-ec11-983e-000d3a33908e/B2tXV68nr_6lraxPmSTeJsZ0O366bCH3mVOxHcDfKcY%21" width="20%" />

---

(C) 2023 Shabang Systems, LLC. Built with ❤️ and 🥗 in the SF Bay Area

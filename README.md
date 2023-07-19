# Quickstart to run the code

**Create a Python virtual environment for dependencies, etc.**
(Only need to do this once per computer)

```
python3 -m venv venv
```

**Ensure virtual environment is activated.**
(Do this each time you start a new terminal session)

```
source venv/bin/activate
```

**Install Python dependencies in virtual environment.**
(Do this whenever dependencies change)

```
pip install -r requirements.txt
```

**Make sure all environment variables are set.**
(Do this whenever you want to run code)

```
python check_environ.py
```

If you don't have a required environment variable set, you'll get a message like this:

```
Not all required environment variables present, some code might not function properly.
Missing vars: OPENAI_KEY, ELASTIC_URL, ELASTIC_USER, ELASTIC_PASSWORD
```

Set those variables through the `.env` file (set values after the = sign in the template) or through simple `export` in your shell, e.g.:

```
export OPENAI_KEY=sk-some-api-key
```

An example of all the environment variables needed is in the .env.example file?

Values set in your shell will override those in the `.env` file.

**Provision your Elastic**

In the future we hope to have better ways of doing this. However, for now, you need to manually seed your schema. To do this, create an ElasticSearch api instance, and call the following once per **new elastic instance**:

```python
from elasticsearch import Elasticsearch
from simon.utils.elastic import _seed_schema

es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
_seed_schema(es)
```

**Run the code!**

```
python playground.py
```

## Misc notes

You'll need java installed/available to run `Tika` which is used for fetching/manipulating external data.

Check that it's available:

```
java -version
```

If not, install is system dependent.

(Quick fix for Ubuntu + Debian-based distros: `sudo apt install default-jre`)

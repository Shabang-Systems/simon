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
(Do this whenever you start a new terminal session + want to run code)

```
python check_environ.py
```

If you don't have a required environment variable set, you'll get a message like this:

```
Not all required environment variables present, some code might not function properly.
Missing vars: OPENAI_KEY, SOMETHING_ELSE
```

Set those variables through the `.env` file (copy `.env.exapmle` and set values after the = sign) or through simple `export` in your shell, e.g.:

```
export OPENAI_KEY=sk-some-api-key
```

An example of all the environment variables needed is in the .env.example file?

Values set in your shell will override those in the `.env` file.

**Provision your Elastic**

You need to manually seed the ElasticSearch schema when you're first setting up. To do this, create an ElasticSearch api instance, and use the following helper script once per **new elastic instance**:

```
python setup_es.py
```

If you find that you want to delete the existing ElasticSearch schema and start fresh, you can use the `--nuke` option:

```
python setup_es.py --nuke
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

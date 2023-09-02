# Detailed Setup Guide
We recommend reading the [quick start guide](../start.md) to get up and running with Simon. This is a document which provides some extra guidance regarding configuring Simon and some more advanced options.

## Database and Credentials
You will need to first setup an instance of Postgresql (**version 15**) on either a remote server or on your local machine. To set it up on your local machine, follow [the instructions available here](https://www.postgresql.org/download/). If setting up remotely, identify and follow the instructions of your cloud provider.

After setting up postgres, install the `vector` plugin [available here](https://github.com/pgvector/pgvector) (and already installed on most major cloud providers—just find instructions on how to enable it) to support Simon. 

You will also need OpenAI credentials. This will be available be either with the OpenAI public API, or Azure OpenAI Services.

Get the postgres connection credentials (for local installations, they are often `localhost:5432`, username `postgres` and no password; please refer to your distribution's instructions) and OpenAI credentials, and keep it for use in the steps below. 

## Java
If you would like to perform OCR or textual extraction from PDFs/impges with Simon, you optionally need Java installed/available to run `Tika` which is used for fetching/manipulating external data.

Check that it's available:

```bash
java -version
```

If not, install is system dependent. Quick fix for Ubuntu + Debian-based distros: `sudo apt install default-jre`. For macOS, run `brew install java` and be sure to follow the "Next Steps"/"Caveats" instructions afterwards.

## Install Simon!
You can install Simon from pypi.

```bash
pip install simon-search
```

all versions are figured with `Python 3.11`; all versions `>3.9` should be supported.

## Set Environment Variables
There are a few secret credentials (database, OpenAI) that we mentioned above. You can manually enter these credentials and configure OpenAI each time you use Simon using the `simon.create_context` function. However, we heavily recommend creating an `.env` file to store the credentials so you don't have type them in each time (or accidentally commit them :p).

To do this, create a `.env` file *in the directory* in which you plan to use Simon. Copy the `.env.example` [available at this link](https://github.com/Shabang-Systems/simon/blob/main/.env.example) and set values after the = sign.

If you don't want to create an `.env` file, you can also use the `export` directive in your bash shell to set all of the environment variables [listed in the file above for the current shell session](https://github.com/Shabang-Systems/simon/blob/main/.env.example).

Values set in your shell will override those in the `.env` file.

## Provision your Database

You need to manually seed the database schema when you're first setting up. There is

### Provisioning with the library
You can provision Simon with Simon itself; to do so, follow the [steps available here the quickstart guide](../start.md/#connect-to-database).

### Provisioning with the CLI setup script
In addition to the programmatic setup above, if you are using the `.env` file to store your credentials, we also built a CLI setup script to set up the tool on your behalf.

To do this, fill out the environment variables found in `.env.example` [available at this link](https://github.com/Shabang-Systems/simon/blob/main/.env.example) into the `.env` file in any local directory, then run in the *same directory* in which you have your `.env` file:

```bash
simon-setup
```

to setup your database. If the program exits without error, you are good to go.

As with before, you can use the `export` directive in your bash shell or inline variable configuration to override or obviate the need to create an `.env` file:


## Run the code!

You are now ready to ~~rock~~ Simon! Follow the usage examples in `tutorial.py` [available here](https://github.com/Shabang-Systems/simon/blob/main/tutorial.py) get a full overview of the Python API.

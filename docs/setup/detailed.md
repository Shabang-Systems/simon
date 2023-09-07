# Setup Details
**To set up Simon, please follow the [quick start instructions](../start.md).** This document aims to provide some specific pointers to each step of the quick start guide. 

This page is not meant to be read from start to finish, refer to specific sections only as needed.

## Database Self-Hosting
FYI: on the sidebar, you can find setup guides available for a selection of cloud databases. If you want to self-host your PostgresSQL instance, read on.

1. You will need to first setup an instance of Postgresql (**version 15**) on either a remote server or on your local machine.
    - To set it up on your local machine, follow [the instructions available here](https://www.postgresql.org/download/).
    - If setting up remotely, identify and follow the instructions of your cloud provider.

2. After setting up postgres, install the `vector` plugin [available here](https://github.com/pgvector/pgvector) (and already installed on most major cloud providers—just find instructions on how to enable it) to support Simon. 

3. Get the postgres connection credentials (for local installations, they are often `localhost:5432`, username `postgres` and no password; please refer to your distribution's instructions) and OpenAI credentials, and keep it for use in the steps below. 

4. Start your PostgreSQL instance, and be sure it's ready to receive requests!

<!-- To set it up on your local machine, follow [the instructions available here](https://www.postgresql.org/download/). If setting up remotely, identify and follow the instructions of your cloud provider. -->

<!-- After setting up postgres, install the `vector` plugin [available here](https://github.com/pgvector/pgvector) (and already installed on most major cloud providers—just find instructions on how to enable it) to support Simon.  -->

<!-- You will also need OpenAI credentials. This will be available be either with the OpenAI public API, or Azure OpenAI Services. -->

<!-- Get the postgres connection credentials (for local installations, they are often `localhost:5432`, username `postgres` and no password; please refer to your distribution's instructions) and OpenAI credentials, and keep it for use in the steps below.  -->

## Java
If you would like to perform OCR or textual extraction from PDFs/impges with Simon, you optionally need Java installed/available to run `Tika` which is used for fetching/manipulating external data.

Check that it's available:

```bash
java -version
```

If not, install is system dependent. Quick fix for Ubuntu + Debian-based distros: `sudo apt install default-jre`. For macOS, run `brew install java` and be sure to follow the "Next Steps"/"Caveats" instructions afterwards.

## Environment Variable Management
`simon.create_context` requires some {OpenAI, database} secrets. In lieu of providing them directly to the function, you can store these in a `.env` file or just set them as environment variables.

To do so, populate [a new file named `.env` following this template](https://github.com/Shabang-Systems/simon/blob/main/.env.example) and place it in the directory where you run python.

In lieu of creating an `.env` file, you can also use the `export` directive in your bash shell to set all of the environment variables [listed in the file above for the current shell session](https://github.com/Shabang-Systems/simon/blob/main/.env.example).

Values set in your shell will override those in the `.env` file.

## Database Provisioning

You need to manually seed the database schema when you're first setting up. There are two options available to help you provision your database.

### Option 1: Provisioning with the library
You can provision Simon with Simon itself; to do so, follow the [steps available here the quickstart guide](../start.md/#connect-to-database).

### Option 2: Provisioning with the CLI setup script
In addition to the programmatic setup above, if you are using the `.env` file to store your credentials, we also built a CLI setup script to set up the tool on your behalf.

To do this, fill out the environment variables found in `.env.example` [available at this link](https://github.com/Shabang-Systems/simon/blob/main/.env.example) into the `.env` file in any local directory, then run in the *same directory* in which you have your `.env` file:

```bash
simon-setup
```

to setup your database. If the program exits without error, you are good to go.

As with before, you can use the `export` directive in your bash shell or inline variable configuration to override or obviate the need to create an `.env` file:


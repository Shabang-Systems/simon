from psycopg2 import connect
from psycopg2.errors import DuplicateTable, InFailedSqlTransaction, FeatureNotSupported

from .environment import get_db_config

import os

import logging
L = logging.getLogger("simon")

def __run_setup(cnx):
    # change working directory to this file (where schema.sql is)
    workdir = os.getcwd() # save temp dir
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    try:
        with cnx.cursor() as cursor:
            cursor.execute(open("schema.sql", "r").read())
    except (DuplicateTable, InFailedSqlTransaction, FeatureNotSupported) as e:
        cnx.rollback()

        if type(e) == DuplicateTable:
            raise ValueError("It looks like you have already created the Simon schema for this database.\nYou only have to call this function once per *database*; no need to call this function every time you use Simon on the same database. You should be able to use the rest of Simon's functions without calling this function again.\n\nAs the recreation of Simon's schema will cause data erasure, if you want to recreate the Simon schema from scratch please manually delete and recreate the database with DROP DATABASE [your database] and CREATE DATABASE [your database] within psql, then invoke this function.")
        elif type(e) == FeatureNotSupported:
            print(e)
            raise ValueError("Hint: is PGVector Setup in the database you used? Follow these instructions: https://github.com/pgvector/pgvector to set up the system if you control the database, or follow instructions by your hosting provider.")
        else:
            return __run_setup(cnx)
    finally:
        cnx.commit()

        # change workdir back
        os.chdir(workdir)

def setup(context):
    """setup simon's necessary tables

    Used for side effects.

    Parameters
    ----------
    context : AgentContext
        The agentcontext to set up the database with.
    """
    
    L.debug("Running Simon setup...") 
    cnx = context.cnx
    __run_setup(cnx)
    L.info("Successfully set up database tables.") 

def execute():
    db_config = get_db_config()

    print()
    print(f"""Welcome to Simon! We are going to set up your database configuration

Please validate the the following information before we continue:
Database Instance: {db_config["host"]}:{db_config["port"]}
Database Name: {db_config["database"]}
Database User: {db_config["user"]}

We will be building a variety of tables and indicies in this database.
Ensure that the user above has full permission to access "{db_config["database"]}"
before continuing.
""")

    input("Tap enter when you are ready.")
    print("")
    
    cnx = connect(**db_config)
    __run_setup(cnx)

    print("All done now. Happy Simoning!")
    print()

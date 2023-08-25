from psycopg2 import connect
from .environment import get_db_config

import os

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

    # change working directory to this file (where schema.sql is)
    workdir = os.getcwd() # save temp dir
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    with cnx.cursor() as cursor:
        cursor.execute(open("schema.sql", "r").read())

    cnx.commit()

    # change workdir back
    os.chdir(workdir)
    print("All done now. Happy Simoning!")
    print()


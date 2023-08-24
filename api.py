"""
api.py
The reference Simon REST API implementation
"""

"""
api.py
A servicable flask API to be able to service Simon.
This should eventually be a larger package, but one file
is fine for now.
"""

# logging
import logging as L

LOG_FORMAT = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
L.basicConfig(format=LOG_FORMAT, level=L.WARNING)
L.getLogger('simon').setLevel(L.DEBUG)

# flask!
import flask
from flask import Flask, request
from flask_cors import cross_origin

# json handling
import json

# importing everything
import simon
from psycopg2 import connect

# decorator business
from functools import wraps

# uuid generator
from uuid import uuid4

simon_api = Flask("simon")
simon_api.config['JSON_SORT_KEYS'] = False
flask.json.provider.DefaultJSONProvider.sort_keys = False

# we first get the database environment
db = simon.environment.get_db_config()
cnx = connect(**db)

# and create a utility function to hydrate a context
def get_key_from_request():
    headers = request.headers.get('Authorization')

    if not headers:
        return None
    
    token = headers.split()[1].strip()

    if token == "":
        return None

    return token

def context(key=None):
    # TODO validate api key here

    if not key:
        key = get_key_from_request()
    if not key:
        return

    # make open ai
    (g3, g4, em) = simon.start.make_open_ai()
    # hydrate!
    context = simon.AgentContext(g3, g4, em, cnx, key)

    return context

def contextify(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        c = context()

        if not c:
            return {
                "status": "error",
                "message": "the UID or API key you provided in the Authorization header is not found or incorrect"
            }, 403

        return f(context=c, *args, **kwds)
    return wrapper

def json_stream(stream):
    for i in stream:
        yield json.dumps(i)

# call the llm directly
@simon_api.route('/query', methods=['GET'])
@cross_origin()
@contextify
def query(context):
    """ask your model a question

    @params
    - q : str --- string question/query to provide to the model
    - response : str --- "stream" to get streaming output

    @headers
    authorization: bearer - context ID

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    arguments = request.args
    q = arguments.get("q", "").strip()
    response = arguments.get("response", "").strip()
    streaming = (response == "streaming")

    if q == "":
        return {
            "status": "error",
            "message": "no query was provided"
        }, 400

    search = simon.Search(context)

    if streaming:
        return json_stream(search.query(q, True)), {"Content-Type": "application/json"}
    else:
        return {
            "response": search.query(q),
            "status": "success"
        }


@simon_api.route('/brainstorm', methods=['GET'])
@cross_origin()
@contextify
def brainstorm(context):
    """make your model underline text and fetch approrpiate resources

    @params
    - q : str --- string question/query to provide to the model
    - response : str --- "stream" to get streaming output

    @headers
    authorization: bearer - context ID

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    arguments = request.args
    q = arguments.get("q", "").strip()
    response = arguments.get("response", "").strip()
    streaming = (response == "streaming")

    if q == "":
        return {
            "status": "error",
            "message": "no query was provided"
        }, 400

    search = simon.Search(context)

    if streaming:
        return json_stream(search.query(q, True)), {"Content-Type": "application/json"}
    else:
        return {
            "response": search.query(q),
            "status": "success"
        }


# remember to close the connection
import atexit
atexit.register(lambda:cnx.close())

# debug 
if __name__ == "__main__":
    simon_api.run()


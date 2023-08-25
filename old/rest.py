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

import threading

# flask!
import flask
from flask import Flask, request, jsonify
from flask_cors import cross_origin

# importing everything
import simon

# uuid generator
from uuid import uuid4

# TODO TODO TODO AUTHHH
# UID = "71e1fed4-9dd8-4525-a3f2-fea4f2ea7bce"
UID = "6ab69096-3bb4-422e-afc5-df032818b3c3" # wiki
# UID = "d075096b-130f-4e35-af70-aa98b41bc1fc" # books
# UID = "4e000ccf-55fd-4793-8966-cfc44cf35516" # discord
# UID = "paper2graph"

# TODO TODO better cache
cache = {}

# create the api object
simon_api = Flask("simon")
simon_api.config['JSON_SORT_KEYS'] = False
flask.json.provider.DefaultJSONProvider.sort_keys = False

context = simon.create_context(UID)
search = simon.Search(context)
management = simon.Datastore(context)

# call the llm directly
@simon_api.route('/query', methods=['GET'])
@cross_origin()
def query():
    """ask your model a question

    @params
    - q : str --- string question/query to provide to the model

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        return {
            "response": search.query(arguments["q"].strip()),
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# call the llm directly, with stream
@simon_api.route('/streamquery', methods=['POST', 'GET'])
@cross_origin()
def streamquery():
    """ask your model a question

    @POST params
    - q : str --- string question/query to provide to the model

    @GET params
    - stream_id : str --- the stream you want to get the results from

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    stream_session = str(uuid4())

    cache[stream_session] = {"output": {"search_results": []},
                             "done": False}

    def callback(x):
        cache[stream_session] = x

    try:
        arguments = request.args
        if request.method == "POST":

            # run the call on a different thread
            thread = threading.Thread(target=search.query,
                                      args=(arguments["q"].strip(), callback))
            thread.start()

            return {
                "stream_id": stream_session,
                "status": "success"
            }
        elif request.method == "GET":
            res = cache.get(arguments["stream_id"].strip(), {})
            return {
                "response": res,
                "status": "success"
            }
            
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400



# engage RIO, which helps brainstorm possible prompts given a textual input
# for instance, while taking notes
@simon_api.route('/brainstorm', methods=['GET'])
@cross_origin()
def brainstorm():
    """brainstorm good resources

    @params
    - q : str --- string query to provide to the model; for instance, a fragment
                  of your notes

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        return {
            "response": search.brainstorm(arguments["q"].strip()),
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400


# call the llm directly, with stream
@simon_api.route('/streambrainstorm', methods=['POST', 'GET'])
@cross_origin()
def streambrainstorm():
    """brainstorm good resources, streaming

    @POST params
    - q : str --- string question/query to provide to the model

    @GET params
    - stream_id : str --- the stream you want to get the results from

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    stream_session = str(uuid4())

    cache[stream_session] = {"output": [], "done": False}

    def callback(x):
        cache[stream_session] = x

    try:
        arguments = request.args
        if request.method == "POST":

            # run the call on a different thread
            thread = threading.Thread(target=search.brainstorm,
                                      args=(arguments["q"].strip(), callback))
            thread.start()

            return {
                "stream_id": stream_session,
                "status": "success"
            }
        elif request.method == "GET":
            res = cache.get(arguments["stream_id"].strip(), {})
            return {
                "response": res,
                "status": "success"
            }
            
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400


@simon_api.route('/fetch', methods=['GET'])
@cross_origin()
def fetch():
    """fetch a document based the hash

    @params
    - resource_id : str --- the hash of the document to fetch
    - session_id : str --- session id that you should have gotten from /start

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        return {
            "response": management.get(arguments["resource_id"].strip()),
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# suggest document title
@simon_api.route('/suggest', methods=['GET'])
@cross_origin()
def suggest():
    """come up with possible documents based on the title

    @params
    - q : str --- the beginning of your query

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        results = search.suggest(arguments["q"].strip())

        return {
            "response": results,
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# automcomplete document title
@simon_api.route('/autocomplete', methods=['GET'])
@cross_origin()
def autocomplete():
    """come up with possible documents based on the title

    @params
    - q : str --- the beginning of your query

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        results = search.autocomplete(arguments["q"].strip())

        return {
            "response": list(set(results)),
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# OCR a document
@simon_api.route('/store', methods=['PUT'])
@cross_origin()
def store():
    """make the assistant store a URL

    @params
    - resource : str --- URL of PDF/text to be read by the assistant
    - title : str --- title of the assistant

    @returns JSON
    - resource_id: str --- string hash representing the ID of the document, useful for /forget
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        return {
            "resource_id": management.store(arguments["resource"].strip(),
                                           title=arguments["title"].strip()),
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# forget a document
@simon_api.route('/forget', methods=['POST'])
@cross_origin()
def forget():
    """make the assistant unread a URL based on the hash

    @params
    - resource_id : str --- the resource ID, given by /read

    @returns JSON:
    - resource_id: str --- string hash representing the ID of the document, useful for /forget
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        management.delete(arguments["resource_id"].strip())

        return {
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# run
if __name__ == "__main__":
    simon_api.run()


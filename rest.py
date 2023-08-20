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
# UID = "6ab69096-3bb4-422e-afc5-df032818b3c3" # wiki
UID = "d075096b-130f-4e35-af70-aa98b41bc1fc" # books
# UID = "4e000ccf-55fd-4793-8966-cfc44cf35516" # discord
# UID = "paper2graph"

# TODO TODO better cache
cache = {}

# create the api object
simon_api = Flask("simon")
simon_api.config['JSON_SORT_KEYS'] = False
flask.json.provider.DefaultJSONProvider.sort_keys = False

# generate new llm
@simon_api.route('/start', methods=['POST'])
@cross_origin()
def start():
    """start a chat instance

    @params
    - providers: str --- optional, provider names to include

    @body

    @returns JSON
    - session_id: UUID --- the UUID to pass to other routes to call this LLM
    - status: str --- status, usually success
    """

    if request.data:
        body = request.json
    else:
        body = {}
    arguments = request.args
    id = str(uuid4())

    try:
        context = simon.create_context(UID)
        cache[id] = {
            "context": context,
            "search": simon.Search(context),
            "management": simon.Datastore(context),
        }

    except KeyError:
        return jsonify({"status": "error",
                        "message": "you are probably missing a required body element"}), 400

    
    return jsonify({"session_id": id,
                    "status": "success"})

# call the llm directly
@simon_api.route('/query', methods=['GET'])
@cross_origin()
def query():
    """ask your model a question

    @params
    - q : str --- string question/query to provide to the model
    - session_id : str --- session id that you should have gotten from /start

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        assistant = cache[arguments["session_id"].strip()]["search"]
        return {
            "response": assistant.query(arguments["q"].strip()),
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
    - session_id : str --- session id that you should have gotten from /start

    @GET params
    - stream_id : str --- the stream you want to get the results from

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    stream_session = str(uuid4())

    cache[stream_session] = {"output": {"search_results": []}}

    def callback(x):
        cache[stream_session] = x

    try:
        arguments = request.args
        if request.method == "POST":
            assistant = cache[arguments["session_id"].strip()]["search"]

            # run the call on a different thread
            thread = threading.Thread(target=assistant.query,
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
    """come up with possible queries

    @params
    - q : str --- string query to provide to the model; for instance, a fragment
                  of your notes
    - session_id : str --- session id that you should have gotten from /start

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        assistant = cache[arguments["session_id"].strip()]["search"]
        return {
            "response": assistant.brainstorm(arguments["q"].strip()),
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
        assistant = cache[arguments["session_id"].strip()]["management"]
        return {
            "response": assistant.get(arguments["resource_id"].strip()),
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
    - session_id : str --- session id that you should have gotten from /start

    @returns JSON
    - response: JSON --- JSON paylod returned from the model
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        assistant = cache[arguments["session_id"].strip()]["search"]
        results = assistant.autocomplete(arguments["q"].strip())

        results_serialized = [{"title": i, "text": j, "resource_id": k} for i,j,k in results]

        return {
            "response": results_serialized,
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
    - session_id : str --- session id that you should have gotten from /start

    @returns JSON
    - resource_id: str --- string hash representing the ID of the document, useful for /forget
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        assistant = cache[arguments["session_id"].strip()]["management"]
        return {
            "resource_id": assistant.store(arguments["resource"].strip(),
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
    - session_id : str --- session id that you should have gotten from /start

    @returns JSON:
    - resource_id: str --- string hash representing the ID of the document, useful for /forget
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        assistant = cache[arguments["session_id"].strip()]["management"]
        assistant.delete(arguments["resource_id"].strip())

        return {
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# run
if __name__ == "__main__":
    simon_api.run()


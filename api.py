"""
api.py
A servicable flask API to be able to service Simon.
This should eventually be a larger package, but one file
is fine for now.
"""

# flask!
from flask import Flask, request, jsonify

# importing everything
from simon import *

# llm tooling
from elasticsearch import Elasticsearch
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

# uuid generator
from uuid import uuid4

# environment
from dotenv import load_dotenv
import os
load_dotenv()

KEY=os.environ["OPENAI_KEY"]
ELASTIC_URL=os.environ["ELASTIC_URL"]
ELASTIC_USER=os.environ["ELASTIC_USER"]
ELASTIC_PASSWORD=os.environ["ELASTIC_PASSWORD"]

# TODO TODO TODO AUTHHH
UID = "test-uid"

# TODO TODO better cache
cache = {}

# create the api object
api = Flask("simon")

# provider input handlers
# they should take the request's arguments + body
# as input, and return an instance of the initialized
# providers
def provider__map(_1, body, _2):
    try:
        key = body["google_maps_key"]
        provider = Map(key.strip())
    except KeyError:
        raise KeyError("simon: missing google_maps_key")

    return provider

PROVIDER_HANDLERS = {
    "map": provider__map
}

# handle provider string for /start
def handle_providers(providers, arguments, body, context):
    """uniform interface to initialize string providers

    Parameters
    ----------
    providers : str
        provider string, seperated by commas, to initialize
    arguments : Dict[str,str]
        the entirety of the request arguments from Flask
    body : Dict[str,str]
        the JSON body of the request
    context : AgentContext
        the LLM context to use 

    Returns
    -------
    List[SimonProvider]
        A list of providers the model can use
    """
    
    providers = [i.strip() for i in providers.split(",") if i.strip() != ""]
    providers = [PROVIDER_HANDLERS[i](arguments, body, context) for i in providers]

    return providers

# generate new llm
@api.route('/start', methods=['POST'])
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
        # get needed variables 
        providers = arguments.get("providers", "")

        # create the base llms
        llm = ChatOpenAI(openai_api_key = KEY,
                         model_name = "gpt-3.5-turbo-0613")
        embeddings = OpenAIEmbeddings(openai_api_key=KEY,
                                      model="text-embedding-ada-002")
        es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))

        # create the context
        context = AgentContext(llm, embeddings, es, UID)

        # get the actual providers from provider string
        providers = handle_providers(providers, arguments, body, context)

        # make the assistant
        assistant = Assistant(context, providers)

        cache[id] = assistant

    except KeyError:
        return jsonify({"status": "error",
                        "message": "you are probably missing a required body element"}), 400

    
    return jsonify({"session_id": id,
                    "status": "success"})

# call the llm directly
@api.route('/chat', methods=['GET'])
def chat():
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
        assistant = cache[arguments["session_id"].strip()]
        return {
            "response": assistant(arguments["q"].strip()),
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# engage RIO, which helps brainstorm possible prompts given a textual input
# for instance, while taking notes
@api.route('/brainstorm', methods=['GET'])
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
        assistant = cache[arguments["session_id"].strip()]
        return {
            "response": assistant.brainstorm(arguments["q"].strip()),
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# OCR a document
@api.route('/read', methods=['PUT'])
def read():
    """make the assistant read a URL

    @params
    - resource : str --- URL of PDF/text to be read by the assistant
    - session_id : str --- session id that you should have gotten from /start

    @returns JSON
    - resource_id: str --- string hash representing the ID of the document, useful for /forget
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        assistant = cache[arguments["session_id"].strip()]
        return {
            "resource_id": assistant.read(arguments["resource"].strip()),
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# store some information
@api.route('/remember', methods=['PUT'])
def remember():
    """make the assistant remember some info

    @params
    - title : str --- the title to store the document
    - content : str --- the content to store
    - session_id : str --- session id that you should have gotten from /start

    @returns JSON
    - resource_id: str --- string hash representing the ID of the document, useful for /forget
    - status: str --- status, usually success
    """

    try:
        arguments = request.args
        assistant = cache[arguments["session_id"].strip()]
        return {
            "resource_id": assistant.store(arguments["title"].strip(),
                                           arguments["content"].strip()),
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# forget a document
@api.route('/forget', methods=['POST'])
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
        assistant = cache[arguments["session_id"].strip()]
        assistant.forget(arguments["resource_id"].strip())

        return {
            "status": "success"
        }
    except KeyError:
        return jsonify({"status": "error",
                        "message": "malformed request, or invalid session_id"}), 400

# run
if __name__ == "__main__":
    api.run()

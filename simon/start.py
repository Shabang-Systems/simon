"""
quick.py
Utilities that act as helper functions
"""

from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings


from psycopg2 import connect

import logging
L = logging.getLogger("simon")

from .models import *
from .environment import get_env_vars, get_db_config

def make_open_ai(openai_api_key:str=None, oai_config:dict=None):
    """Create OpenAI configuration

    Parameters
    ----------
    openai_api_key : optional, str
        OpenAI API key to use, or read from enviroment variable.
    oai_config : optional, str
        Openai configuration, used for Azure

    Returns
    -------
    AgentContext
        The context that used for all other Simon operations.
    """

    if (not openai_api_key) and (not oai_config):
        env_vars = get_env_vars()
        oai_config = env_vars.get('OAI_CONFIG')
    else:
        if not oai_config:
            oai_config = {}
            oai_config["openai_api_key"] = openai_api_key

    # create openai stuff
    if oai_config and oai_config.get("openai_api_type", "") == "azure":
        L.warning("Simon's Azure Intelligence Service API is *UNSTABLE* ALPHA as of now. Expect things to break.")
        L.warning("We recommend you use the public OpenAI Endpoint, if possible.")
        gpt3 = AzureChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, **oai_config,
                               deployment_name="gpt-35-turbo")
        gpt4 = AzureChatOpenAI(model_name="gpt-4", temperature=0, **oai_config,
                               deployment_name="gpt-4")
        embedding = OpenAIEmbeddings(model="text-embedding-ada-002", **oai_config,
                                     deployment="text-embedding-ada-002")
    else:
        gpt3 = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=oai_config["openai_api_key"])
        gpt4 = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=oai_config["openai_api_key"])
        embedding = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=oai_config["openai_api_key"])

    return (gpt3, gpt4, embedding)


def create_context(uid:str, openai_api_key:str=None,
                   db_config:dict=None, oai_config:dict=None,
                   ssl:bool=False):
    """Quickstart function to build a Simon context with OpenAI

    Parameters
    ----------
    uid : str
        User ID to use.
    openai_api_key : optional, str
        OpenAI API key to use, or read from enviroment variable.
    db_config : optional, dict
        Posgres configuration to use (keys used to seed Posgres), or
        read from enviroment variables.
    oai_config : optional, dict
        Full OpenAI Config
    ssl : optional, bool
        Whether to forcibly connect to SSL.

    Returns
    -------
    AgentContext
        The context that used for all other Simon operations.
    """

    if (not db_config):
        db_config = get_db_config()

    (gpt3, gpt4, embedding) = make_open_ai(openai_api_key, oai_config)

    # create db instance
    if ssl:
        cnx = connect(**db_config, sslmode='require')
    else:
        cnx = connect(**db_config)

    # build a context!
    context = AgentContext(gpt3, gpt4, embedding, cnx, uid)

    return context


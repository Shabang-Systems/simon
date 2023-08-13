"""
quick.py
Utilities that act as helper functions
"""

from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from elasticsearch import Elasticsearch

import logging
L = logging.getLogger("simon")

from .models import *
from .environment import get_env_vars

def create_context(uid:str, openai_api_key:str=None, es_config:dict=None,
                   openai_api_base:str=None):
    """Quickstart function to build a Simon context with OpenAI

    Parameters
    ----------
    uid : str
        User ID to use for Elastic.
    openai_api_key : optional, str
        OpenAI API key to use, or read from enviroment variable.
    es_config : optional, dict
        Elastic configuration to use (keys used to seed ElasticSearch), or
        read from enviroment variables.

    Returns
    -------
    AgentContext
        The context that used for all other Simon operations.
    """

    if (not openai_api_key) or (not es_config):
        env_vars = get_env_vars()
        es_config = env_vars.get('ES_CONFIG')
        oai_config = env_vars.get('OAI_CONFIG')

    # create openai stuff
    if oai_config.get("openai_api_type", "") == "azure":
        L.warn("Simon's Azure API is *UNSTABLE* PRE_ALPHA as of now. Expect things to break.")
        L.warn("We recommend you use the public OpenAI Services, if possible.")
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

    # create elastic instance
    es = Elasticsearch(**es_config)

    # build a context!
    context = AgentContext(gpt3, gpt4, embedding, es, uid)

    return context


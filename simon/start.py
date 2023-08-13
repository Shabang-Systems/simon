"""
quick.py
Utilities that act as helper functions
"""

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from elasticsearch import Elasticsearch

from .models import *
from .environment import get_env_vars

def create_context_oai(uid:str, openai_key:str=None, es_config:dict=None):
    """Quickstart function to build a Simon context with OpenAI

    Parameters
    ----------
    uid : str
        User ID to use for Elastic.
    openai_key : optional, str
        OpenAI key to use, or read from enviroment variable.
    es_config : optional, dict
        Elastic configuration to use (keys used to seed ElasticSearch), or
        read from enviroment variables.

    Returns
    -------
    AgentContext
        The context that used for all other Simon operations.
    """

    if (not openai_key) or (not es_config):
        env_vars = get_env_vars()
        openai_key = env_vars.get("OPENAI_KEY")
        es_config = env_vars.get('ES_CONFIG')

    # create openai stuff
    gpt3 = ChatOpenAI(openai_api_key=openai_key, model_name="gpt-3.5-turbo", temperature=0)
    gpt4 = ChatOpenAI(openai_api_key=openai_key, model_name="gpt-4", temperature=0)
    embedding = OpenAIEmbeddings(openai_api_key=openai_key, model="text-embedding-ada-002")

    # create elastic instance
    es = Elasticsearch(**es_config)

    # build a context!
    context = AgentContext(gpt3, gpt4, embedding, es, uid)

    return context


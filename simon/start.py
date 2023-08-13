"""
quick.py
Utilities that act as helper functions
"""

from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from elasticsearch import Elasticsearch

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
    if oai_config.get("openai_api_type", "").lower() == "azure":
        gpt3 = AzureChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, **oai_config)
        gpt4 = AzureChatOpenAI(model_name="gpt-4", temperature=0, **oai_config)
    else:
        gpt3 = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, **oai_config)
        gpt4 = ChatOpenAI(model_name="gpt-4", temperature=0, **oai_config)
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002", **oai_config)

    # create elastic instance
    es = Elasticsearch(**es_config)

    # build a context!
    context = AgentContext(gpt3, gpt4, embedding, es, uid)

    return context


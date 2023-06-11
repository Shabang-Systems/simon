"""
kb.py
Knowledge Indexing Toolkit.
"""


# langchain stuff
from langchain.tools import Tool, StructuredTool
from langchain.embeddings.base import Embeddings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


# utilities
from ..utils.elastic import *
from ..models import *
from ..components.documents import *


class KnowledgebaseToolkit():
    """A set of tools"""

    def __init__(self, context:AgentContext):
        self.context = context

    def get_tools(self):
        def __lookup(query, context):
            results = search(query, context)
            if len(results) == 0:
                return "Nothing relating to your question is found in the knowledgebase."
            return assemble_chunks(results, context)

        lookup = Tool.from_function(func=lambda q:__lookup(q, self.context),
                                    name="knowledgebase_lookup",
                                    description="Useful for when you need to look up a fact from your existing knowledge base. Provide a natural language question, using specific keywords that may already appear in the knowledge base. For instance, if you want to know about self attention, ask \"what is self attention?\" Provide this tool only the question. Do not add qualifications. This tool does not remember the past, so when asking a follow up question, provide the entire context for previous questions in your new question.")

        return lookup

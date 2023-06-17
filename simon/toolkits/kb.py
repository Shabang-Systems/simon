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


class KnowledgebaseToolkit(SimonToolkit):
    """A set of tools"""

    prefix="knowledgebase"

    def __init__(self, context:AgentContext):
        self.context = context
        self.__lastdoc = None

    @property
    def tools(self):
        def __lookup(query, context):
            results = search(query, context)
            if len(results) == 0:
                return "Nothing relating to your question is found in the knowledgebase."
            return assemble_chunks(results, context)

        lookup = Tool.from_function(func=lambda q:__lookup(q, self.context),
                                    name="knowledgebase_lookup",
                                    description="Useful for when you need to look up a fact from your existing knowledge base. Provide a natural language statement (i.e. not a question), using specific keywords that may already appear in the knowledge base. Provide this tool only the statement. Do not ask the tool a question. The knowledgebase can only give you facts, and cannot do things for you.")

        def __store(q):
            res = q.split("|||")
            key = res[0]
            source = res[1]
            value = res[2]
            key = key.strip("|").strip("\"").strip()
            source = source.strip("|").strip("\"").strip()
            value = value.strip("|").strip("\"").strip()

            document = parse_text(value, key, source)
            hash = index_document(document, self.context)

            return f"{value}"

        memory_store_tool = Tool.from_function(func = lambda q: __store(q),
                                               name="knowledgebase_store",
                                               description="Use this tool to store a piece of information into memory. Provide this tool with a list of three elements, seperated by three pipes (|||). The three elements of the list should be: title of knowledge, a brief description of the source, and the actual knowledge. For example, if you want to store the recipe for Mint Fizzy Water, you should provide this tool Mint Fizzy Water Recipe|||cookistry.com|||Two tablespoons mint simple syrup\nCold water to fill PureFizz Soda Maker to proper level\nAdd ingredients to soda maker. Do not use this tool to present information to the user. They are only stored for YOU to remember in the future, not for the user.")

        return [lookup, memory_store_tool]

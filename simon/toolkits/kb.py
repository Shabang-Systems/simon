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

    @property
    def tools(self):
        def __lookup(query, context):
            results = search(query, context)
            if len(results) == 0:
                return "Nothing relating to your question is found in the knowledgebase."
            return assemble_chunks(results, context)

        lookup = Tool.from_function(func=lambda q:__lookup(q, self.context),
                                    name="knowledgebase_lookup",
                                    description="Useful for when you need to look up a fact from your existing knowledge base. Provide a natural language statement, using specific keywords that may already appear in the knowledge base. For instance, if you want to know about self attention, ask \"self attention definition\" Provide this tool only the statement. Do not ask the tool a question. This tool does not remember the past, so when asking a follow up question, provide the entire context for previous questions in your new question.")

        def __read(url, type):
            hash = read_remote(url, self.context, type)
            top = top_tf(hash, self.context)
            return f"=== URL: {url}, hash: `{hash}` ===\n"+"\n".join(top)

        read_doc = Tool.from_function(func=lambda q:__read(q.strip("\"").strip(), MediaType.DOCUMENT),
                                    name="knowledgebase_summarize_doc",
                                    description="Useful for when you need to read the main idea of an online document. Provide this tool a URL link to the document you wish to read. So, your input to this tool should begin with http, and include ONLY the full URL to the document and nothing else. This tool accepts PDF documents, text documents, as well as most types of images. It will return the most important passages of the document, as well as a hash identifying the document surrounded by backtics like this: `{hash here}`. This tool does NOT return the full document; so, to ask follow-up questions in the document, pass your follow up and the hash to knowledgebase_answer_question_with_doc tool and follow the instructions there.")

        def __followup(q):
            hash, q = q.split(",")
            hash = hash.strip("`").strip("\"").strip()
            q = q.strip("`").strip("\"").strip()
            results = search(q, self.context, doc_hash=hash)
            if len(results) == 0:
                return "Nothing relating to your question is found in the knowledgebase."
            return assemble_chunks(results, self.context)

        followup = Tool.from_function(func=lambda q:__followup(q),
                                    name="knowledgebase_answer_question_with_doc",
                                    description="Useful when you need to answer a question about or using a particular document. First, obtain the hash of the resource using knowledgebase_summarize_doc. Then, provide this tool with a list of two elements, seperated by a comma. The first element is a hash identifing the document you obtained from knowledgebase_summarize_doc or knowledgebase_read_web. The second element is your query: it should be a statement using keywords that may appear in the document. For instance, if you want to ask 'what is self attention' from a paper you read with the hash 067cebac263d34cfca44e22239f40f4bd8bfb09f15a9e03af6b098000383b2f7, you would pass this tool 067cebac263d34cfca44e22239f40f4bd8bfb09f15a9e03af6b098000383b2f7, self attention defition.")

        return [lookup, read_doc, followup]

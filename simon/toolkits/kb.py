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
                                    description="Useful for when you need to look up a fact from your existing knowledge base. Provide a natural language statement (i.e. not a question), using specific keywords that may already appear in the knowledge base. Provide this tool only the statement. Do not ask the tool a question. This tool does not remember the past, so when asking a follow up question, provide the entire context for previous questions in your new question.")

        def __read(url, type):
            hash = read_remote(url, self.context, type)
            top = top_tf(hash, self.context)
            self.__lastdoc = hash
            return f"=== URL: {url}, hash: `{hash}` ===\n"+"\n".join(top)

        read_doc = Tool.from_function(func=lambda q:__read(q.strip("\"").strip(), MediaType.DOCUMENT),
                                    name="knowledgebase_summarize_doc",
                                    description="Useful for when you need to read the main idea of an online document. Provide this tool a URL link to the document you wish to read. So, your input to this tool should begin with http, and include ONLY the full URL to the document and nothing else. This tool accepts PDF documents, text documents, as well as most types of images. It will return the most important passages of the document, as well as a hash identifying the document surrounded by backtics like this: `{hash here}`. This tool does NOT return the full document; so, to ask follow-up questions in the document, pass your follow up and the hash to knowledgebase_answer_question_with_doc tool and follow the instructions there.")

        def __followup(q):
            if self.__lastdoc:
                return "You didn't read a document first using knowledgebase_summarize_doc! We don't know what document you are talking about." 
            q = q.strip("`").strip("\"").strip()
            results = search(q, self.context, doc_hash=self.__lastdoc)
            if len(results) == 0:
                return "Nothing relating to your question is found regarding your question."
            return assemble_chunks(results, self.context)

        followup = Tool.from_function(func=lambda q:__followup(q),
                                    name="knowledgebase_followup_doc",
                                    description="Useful for when you need to look up more specific information about the document you just read using knowledgebase_summarize_doc. Provide a natural language statement (i.e. not a question), using specific keywords that may already appear in the document. Do not use this tool before using knowledgebase_summarize_doc first to read a document, otherwise we won't know what document you are talking about.")

        return [lookup, read_doc, followup]

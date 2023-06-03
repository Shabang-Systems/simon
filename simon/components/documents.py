"""
documents.py
Components for document parsing.
"""

# System Library
import os
import time
import hashlib
from tempfile import TemporaryDirectory

# Networking
import requests

# langchain stuff
from langchain.embeddings.base import Embeddings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# tika
from tika import parser

# utilities
from ..utils.elastic import *
from ..models import *

#### PARSERS ####
def parse_tika(uri) -> ParsedDocument:
    """Parse a local document using Tika and Tesseract

    Parameters
    ----------
    uri : str
        The LOCAL URI where the document lives to be parsed.

    Returns
    -------
    ParsedDocument
        The parsed document.
    """
    # parse data
    parsed = parser.from_file(uri)
    meta = {
        "source": parsed["metadata"]["resourceName"],
        "title": parsed["metadata"].get("pdf:docinfo:title"),
    }
    # clean the chunks
    parsed_chunks = [i.replace("\n"," ").replace("  ", " ").strip()
                     for i in parsed["content"].split("\n\n") if i != '']
    # and also create the bigger document
    parsed_text = " ".join(parsed_chunks)
    # hash the text
    hash = hashlib.sha256(parsed_text.encode()).hexdigest()

    # return!
    return ParsedDocument(parsed_text, parsed_chunks, hash, meta)

#### GETTERS ####
def get_cached_hash(uri:str, context:AgentContext):
    """Get the hash of a possibly indexed document.

    Parameters
    ----------
    uri : str
        The string hash to read.
    context : AgentContext
        The context pointer to use to perform parsing.

    Return
    ------
    Optional[str]
        str hash, or None.
    """

    hash = None
    results = context.elastic.search(index="simon-cache",
                                     query={"bool": {"must": [{"term": {"uri": uri}},
                                                              {"term": {"user.keyword":
                                                                        context.uid}}]}})["hits"]
    if results["total"]["value"] > 0:
        hash = results["hits"][0]["_source"]["hash"]
    return hash

def get_cached_fulltext(hash:str, context:AgentContext):
    """Read a document possibly stored in the cache.

    Parameters
    ----------
    hash : str
        The string hash to read.
    context : AgentContext
        The context pointer to use to perform parsing.

    Return
    ------
    Optional[str]
        str full text, or None.
    """

    doc = context.elastic.search(index="simon-fulltext",
                                 query={"bool": {"must": [{"term": {"hash": hash}},
                                                          {"term": {"user.keyword":
                                                                     context.uid}}]}},
                                 fields=["text"], size=1)
    hits = [i["fields"]["text"][0] for i in doc["hits"]["hits"]]

    if len(hits) > 0: return hits[0]

def search_cached(keywords:str, context:AgentContext):
    """Search a document possibly stored in the cache.

    Parameters
    ----------
    hash : str
        The string hash to read.
    context : AgentContext
        The context pointer to use to perform parsing.
    full : 

    Return
    ------
    Optional[str]
        str full text, or None.
    """

    doc = context.elastic.search(index="simon-fulltext",
                                 query={"bool": {"must": [{"match": {"hash": hash}},
                                                          {"term": {"user.keyword":
                                                                     context.uid}}]}},
                                 fields=["text"], size=1)
    hits = [i["fields"]["text"][0] for i in doc["hits"]["hits"]]

    if len(hits) > 0: return hits[0]

def search(query:str, context:AgentContext, search_type=IndexClass.CHUNK,
           doc_hash=None, k=5, threshold=1):
    """ElasticSearch the database based on a query!

    Parameters
    ----------
    query : str
        The query to ask.
    context : AgentContext
        Context pointer to be used for operations.
    search_type : IndexClass
        Which index to search. Options include
        IndexClass.CHUNK or IndexClass.FULLTEXT.
    doc_hash : str
        The document (in hashed form) to limit search on.
    k : optional, int
        Number of values to return.
    threshold : optional, float
        Threshold of score before a value is returned.

    Return
    ------
    List[str]
        Results of the search.
    """

    # get results
    squery = {
        "bool": {"must": [
            {"term": {"user.keyword": context.uid}},
            {"match": {"text": query}}
        ]}
    }
    if doc_hash:
        squery["bool"]["must"].append({"term": {"hash": doc_hash}})

    results = context.elastic.search(index=search_type.value, query=squery,
                                     fields=["text", "metadata"], size=str(k))
    results = [{"text": i["fields"]["text"][0],
                "metadata": i["fields"]["metadata"][0]}
               for i in results["hits"]["hits"] if i["_score"] > threshold]

    return results

#### SETTERS ####
def index_document(doc:ParsedDocument, context:AgentContext):
    """Indexes a document, if needed.

    Parameters
    ----------
    doc : ParsedDocument
        Document to Index.
    context : AgentContext
        Information about data stores, etc. which determines
        the context.

    Note
    ----
    Why is this code so agressive about search/checking first
    before indexing? Because indexing is SIGNIFICANTLY more
    expensive in Elastic than reading. Because its a search db
    after all.
    """

    # And check if we have already indexed the doc
    indicies = context.elastic.search(index="simon-fulltext",
                                      query={"bool": {"must": [{"term": {"hash": doc.hash}},
                                                               {"term": {"user.keyword":
                                                                         context.uid}}]}})["hits"]
    # If not, do so!
    if indicies["total"]["value"] == 0:
        context.elastic.index(index="simon-fulltext",
                              document={"user": context.uid,
                                        "metadata": doc.meta,
                                        "hash": doc.hash,
                                        "text": doc.main_document})
        context.elastic.indices.refresh(index="simon-fulltext")

    # And check if we have already indexed the doc
    indicies = context.elastic.search(index="simon-paragraphs",
                                      query={"bool": {"must": [{"term": {"hash": doc.hash}},
                                                               {"term": {"user.keyword":
                                                                         context.uid}}]}})["hits"]
    # If not, do so!
    if indicies["total"]["value"] == 0:
        update_calls = [{"_op_type": "index",
                        "_index": "simon-paragraphs",
                        "user": context.uid,
                        "metadata": doc.meta,
                        "hash": doc.hash,
                        "text": i} for i in doc.paragraphs]

        bulk(context.elastic, update_calls)

#### SPECIAL SETTERS ####
def index_remote_file(url:str, context:AgentContext):
    """Read and index a remote file into Elastic by trying really hard not to actually read it.

    Parameters
    ----------
    url : str
        URL to read.
    context : AgentContext
        Context to use.

    Return
    ------
    str
        Hash of the file we are reading, useful for searching, etc.
    """

    # Search for the URL in the cache if it exists
    hash = get_cached_hash(url, context)

    # If there is no cache retrieve the doc
    if not hash:
        # Retrieve and parse the document
        with TemporaryDirectory() as tmpdir:
            f = os.path.join(tmpdir, f"simon-cache-{time.time()}")
            headers = {'user-agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers)
            with open(f, 'wb') as fp:
                fp.write(r.content)
            doc = parse_tika(f)
            hash = doc.hash

        # and pop it into the cache
        context.elastic.index(index="simon-cache", document={"uri": url, "hash": hash})
        context.elastic.indices.refresh(index="simon-cache")

        index_doc(doc, context)

    # retrun hash
    return hash

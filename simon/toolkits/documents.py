# langchain stuff
from langchain.tools import Tool, StructuredTool
from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import hashlib

# images and numpy
import numpy as np
from PIL import Image

# mmm
import os
import time
import json
import shutil
import requests
import subprocess
from glob import glob
from typing import List, Dict
from tempfile import TemporaryDirectory

# tika
from tika import parser

# dataclasses
from dataclasses import dataclass

# constants to identify the pdffigures executable
# __file__ = "./simon/toolkits/documents.py"
FILEDIR = os.path.dirname(os.path.abspath(__file__))
# path to java
# TODO change this at will or put in .env 
JARDIR = os.path.abspath( 
    os.path.join(FILEDIR, "../opt/pdffigures2.jar"))
JAVADIR = os.path.realpath(shutil.which("java"))

@dataclass
class TikaDocument:
    main_document: str
    paragraphs: List[str]
    hash: str
    meta: Dict

def parse_document(uri) -> TikaDocument:
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
    return TikaDocument(parsed_text, parsed_chunks, hash, meta)

def parse_figures(target):
    """Extract figures from PDF file with pdffigures2.

    Parameters
    ----------
    target : str
        The file to get figures from.

    Returns
    -------
    list
        A list dictionaries containing figures, their captions, and a numpy array for the figure.
    """

    # get full path of target
    target_path = os.path.abspath(target)

    # store temporary directory
    wd = os.getcwd()
    # create and change to temporary directory
    with TemporaryDirectory() as tmpdir:
        # change into temproary directory and extract figures
        os.chdir(tmpdir)
        subprocess.check_output(f"java -jar {JARDIR} -g meta -m fig {target_path} -q", shell=True)

        # read the metadata file
        meta_path = glob("meta*.json")[0]
        with open(meta_path, 'r') as df:
            meta = json.load(df)

        # open each of the images as numpy
        for figure in meta["figures"]:
            img = Image.open(figure["renderURL"])
            figure["render"] = np.array(img)
            img.close()

    # change directory back
    os.chdir(wd)

    return meta["figures"]

def store(doc:TikaDocument, es:Elasticsearch, embedding:Embeddings, user:str):
    """Utility to stored parsed document.

    Parameters
    ----------
    doc : TikaDocument
        The document to store into elastic.
    es : Elasticsearch
        Elastic search instance used to store the data.
    embedding : Embeddings
        Text embedding model to use.
    user : str
        The UID.
    """
    embedded = embedding.embed_documents(doc.paragraphs)
    docs = [{"embedding": a,
             "text": b}
            for a,b in zip(embedded, doc.paragraphs)]
    update_calls = [{"_op_type": "index",
                     "_index": "simon-docs",
                     "user": user,
                     "metadata": doc.meta,
                     "hash": doc.hash,
                     "doc": i} for i in docs]
    update_calls.append({"_op_type": "index",
                         "_index": "simon-fulltext",
                         "user": user,
                         "metadata": doc.meta,
                         "hash": doc.hash,
                         "text": doc.main_document})
    bulk(es, update_calls)

def _seed_schema(es:Elasticsearch, dim=1546):
    """Hidden function to seed the index.

    Parameters
    ----------
    es : Elasticsearch
        Elastic search instance used to store the data.
    dim : int
        The dimension of the output.
    """
    es.indices.create(index="simon-cache", mappings={"properties": {"uri": {"type": "keyword"},
                                                                    "hash": {"type": "text"}}})
    es.indices.create(index="simon-docs", mappings={"properties": {"doc.embedding": {"type": "dense_vector",
                                                                                     "dims": 1536,
                                                                                     "similarity": "cosine",
                                                                                     "index": "true"}}})
def read(hash:str, es:Elasticsearch, uid:str):
    """Read a document stored in the cache

    Parameters
    ----------
    hash : str
        The string hash to read.
    es : Elasticsearch
        The elastic instance to search on.
    uid : str
        User's ID.

    Return
    ------
    Optional[str]
        str full text, or None.
    """

    doc = es.search(index="simon-fulltext", query={"bool": {"must": [{"match": {"hash": hash}},
                                                                {"match": {"user.keyword": uid}}]}},
                    fields=["text"], size=1)
    hits = [i["fields"]["text"][0] for i in doc["hits"]["hits"]]

    if len(hits) > 0: return hits[0]

def nl_search(query:str,es:Elasticsearch, embedding:Embeddings, user:str, doc_hash=None, k=5, threshold=0.9):
    """ElasticSearch the database based on natural language query!

    Parameters
    ----------
    query : str
        The query to ask.
    es : Elasticsearch
        Elastic search instance used to store the data.
    embedding : Embeddings
        Text embedding model to use.
    user : str
        The UID to search.
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
    q = embedding.embed_query(query)
    kquery = {"field": "doc.embedding",
              "query_vector": q,
              "k": k,
              "num_candidates": 800,
              "filter": []}
# {"term": {"user.keyword": user}}
    if doc_hash:
        kquery["filter"].append({"term": {"hash": doc_hash}})
    results = es.search(index="simon-docs", knn=kquery)
    # parcel out valid results
    results = [i["_source"]["doc"]["text"] for i in results["hits"]["hits"] if i["_score"] > threshold]

    return results 

def bm25_search(query:str,es:Elasticsearch, embedding:Embeddings, user:str, doc_hash=None, k=5, threshold=1):
    """ElasticSearch the database based on natural language query!

    Parameters
    ----------
    query : str
        The query to ask.
    es : Elasticsearch
        Elastic search instance used to store the data.
    embedding : Embeddings
        Text embedding model to use.
    user : str
        The UID to search.
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
    q = embedding.embed_query(query)
    squery = {
        "bool": {"must": [
            # {"term": {"user.keyword": user}}, #TODO fix user authentication mess
            {"match": {"doc.text": query}}
        ]}
    }
    if doc_hash:
        squery["bool"]["must"].append({"term": {"hash": doc_hash}})
    results = es.search(index="simon-docs", query=squery, fields=["doc.text"], size=str(k))
    # parcel out valid results
    results = [i["fields"]["doc.text"][0] for i in results["hits"]["hits"] if i["_score"] > threshold]

    return results 

def __check_hash_exists(url:str, es:Elasticsearch):
    hash = None
    results = es.search(index="simon-cache", query={"match": {"uri": url}})["hits"]
    if results["total"]["value"] > 0:
        hash = results["hits"][0]["_source"]["hash"]

    return hash

def __index_doc_with_check(doc:TikaDocument, es:Elasticsearch, embedding:Embeddings, user:str):
    hash = doc.hash

    # And check if we have already indexed the doc
    indicies = es.search(index="simon-docs", query={"bool": {"must": [{"match": {"hash": hash}},
                                                                      {"match": {"user.keyword": user}}]}})["hits"]
    # If not, do so!
    if indicies["total"]["value"] == 0:
        store(doc, es, embedding, user)
        es.indices.refresh(index="simon-docs")

    return hash

def index_remote_file(url:str, es:Elasticsearch, embedding:Embeddings, user:str):
    """Read and index a remote file into Elastic by trying really hard not to actually read it.

    Parameters
    ----------
    url : str
        URL to read.
    es : Elasticsearch
        Elastic search instance used to store the data.
    embedding : Embeddings
        Text embedding model to use.
    user : str
        The UID to search.

    Return
    ------
    str
        Hash of the file we are reading, useful for searching, etc.
    """

    # Search for the URL in the cache if it exists
    hash = __check_hash_exists(url, es)

    # If there is no cache retrieve the doc
    if not hash:
        # Retrieve and parse the document
        with TemporaryDirectory() as tmpdir:
            f = os.path.join(tmpdir, f"simon-cache-{time.time()}")
            headers = {'user-agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers)
            with open(f, 'wb') as fp:
                fp.write(r.content)
            doc = parse_document(f)
            hash = doc.hash

        # and pop it into the cache
        es.index(index="simon-cache", document={"uri": url, "hash": hash})

        __index_doc_with_check(doc, es, embedding, user)

    # retrun hash
    return hash


def kv_get(key:str, es:Elasticsearch, user:str, return_id=False):
    """Performs a key-value search on the Elastic store

    Parameters
    ----------
    key : str
        The key to search for. 
    es : Elasticsearch
        The Elastic instance.
    user : str
        UID.
    return_id : bool
        Whether to return ID or just return result.

    Return
    ------
    Optional[str] or Optional[Tuple[str, str]]
        None if not found, value, or (value, id).
    """

    results = es.search(index="simon-kv", query={"bool":
                                                 {"must": [{"term": {"key": key}},
                                                           {"term": {"user.keyword": user}}]}}, size=1)
    if len(results["hits"]["hits"]) == 0:
        return (None,None) if return_id else None

    result = results["hits"]["hits"][0]

    if return_id: return result["_source"]["value"], result["_id"]
    else: return result["_source"]["value"]

def kv_set(key:str, value:str, es:Elasticsearch, user:str):
    """Performs a key-value search on the Elastic store

    Parameters
    ----------
    key : str
        The key 
    key : str
        The desired value.
    es : Elasticsearch
        Elastic.
    user : str
        UID
    """

    _,id = kv_get(key, es, user, True)
    if id:
        es.update(index="simon-kv", id=id, doc={"key": key,
                                                "value": value,
                                                "user": user})
    else:
        es.index(index="simon-kv", document={"key": key,
                                             "value": value,
                                             "user": user})
    es.indices.refresh(index="simon-kv")

def kv_delete(key:str, es:Elasticsearch, user:str):
    """Delete a key-value"""

    _,id = kv_get(key, es, user, True)
    if id:
        es.delete(index="simon-kv", id=id)
    es.indices.refresh(index="simon-kv")

class DocumentProcessingToolkit():
    """A set of tools to process documents"""

    def __init__(self, elastic:Elasticsearch, embedding:Embeddings, user:str):
        self.es = elastic
        self.em = embedding
        self.uid = user

    def get_tools(self):
        keyword_lookup = Tool.from_function(func=lambda q:"\n".join(bm25_search(q, self.es, self.em, self.uid)),
                                    name="documents_keyword_search",
                                    description="Useful for when you need to lookup the user's knowledge base with keywords. Provide this tool only relavent keywords that would appear in the database.")

        lookup = Tool.from_function(func=lambda q:"\n".join(nl_search(q, self.es, self.em, self.uid)),
                                    name="documents_lookup_all",
                                    description="Useful for when you need to gather information to answer a question using every file ever seen by the user. Provide a properly-formed question to the tool. This tool doesn't return an answer; instead, it responds with some text that you can read to better help answer the question.")

        def lookup_file_f(q):
            try:
                read_remote = index_remote_file(q.replace("`", "").split(",")[0].strip(),
                                                self.es, self.em, self.uid)
            except ConnectionError:
                return "Hmmm... We don't seem to able to open this file. Can you try another one?"

            result = "\n".join(nl_search(q.replace("`", "").split(",")[1].strip(), self.es, self.em, self.uid,
                                         doc_hash=read_remote))
            return result

        lookup_file =  Tool.from_function(func=lookup_file_f,
                                    name="documents_lookup_file",
                                    description="Useful for when you need to gather information useful for answering a question using a file on the internet. The input to this tool should be a comma seperated list of length two; the first element of that list should be the URL of the file you want to read, and the second element of that list should be question. For instance, `https://arxiv.org/pdf/1706.03762,What is self attention?` would be the input if you wanted to look up the answer to the question of \"What is self attention\" from the PDF located in the link https://arxiv.org/pdf/1706.03762. Provide a properly-formed question to the tool. This tool doesn't return an answer; instead, it responds with some text that you can read to better help answer the question.")

        return [lookup, keyword_lookup, lookup_file]


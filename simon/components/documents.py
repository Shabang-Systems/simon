"""
documents.py
Components for document parsing.
"""

# System Library
import os
import re
import time
import hashlib
import mimetypes
from typing import List
from itertools import groupby, islice
from tempfile import TemporaryDirectory


import logging
L = logging.getLogger("simon")

# Networking
import requests

# langchain stuff
from langchain.embeddings.base import Embeddings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# nltk
from nltk import sent_tokenize

# tika
from tika import parser

# soup
from bs4 import BeautifulSoup

# TFIDF
from sklearn.feature_extraction.text import TfidfVectorizer


# utilities
import json

from .elastic import *
from ..models import *

#### SANITIZERS ####
def __chunk(text, delim="\n\n"):

    sentences = sent_tokenize(text)
     
    # makes groups of 5 sentences, joined, as the chunks
    parsed_chunks = [re.sub(r" +", " "," ".join(sentences[i:i+3]).strip().replace("\n", " ")).strip()
                        for i in range(0, len(sentences), 3)]

    # and also create the bigger document
    parsed_text = "\n".join(parsed_chunks)
    # hash the text
    hash = hashlib.sha256(parsed_text.encode()).hexdigest()

    return parsed_chunks, parsed_text, hash

#### PARSERS ####
def parse_text(text, title=None, source=None, delim="\n\n") -> ParsedDocument:
    """Base parser. Just chunk the text and be done.

    Parameters
    ----------
    text : str
        The raw text to be parsed.
    title : str
        Force a specific title.
    source : str 
        Force a specific source.
    delim : optional, str
        An optional delimiter, if needed.

    Returns
    -------
    ParsedDocument
        The parsed document.
    """

    meta = {
        "source": source,
        "title": title,
    }

    # clean the chunks
    parsed_chunks, parsed_text, hash = __chunk(text, delim)

    # return!
    return ParsedDocument(parsed_text, parsed_chunks, meta)

def parse_tika(uri, title=None, source=None) -> ParsedDocument:
    """Parse a local document using Tika and Tesseract

    Parameters
    ----------
    uri : str
        The LOCAL URI where the document lives to be parsed.
    title : str
        Force a specific title.
    source : str 
        Force a specific source.

    Returns
    -------
    ParsedDocument
        The parsed document.
    """
    # parse data
    parsed = parser.from_file(uri)

    # get metadata
    source = source if source else parsed["metadata"]["resourceName"]
    title = title if title else parsed["metadata"].get("pdf:docinfo:title")

    return parse_text(parsed["content"], title, source)

def parse_web(html, title=None, source=None) -> ParsedDocument:
    """Parse a web page using BeautifulSoup.

    Parameters
    ----------
    html : str
        The raw HTML to be parsed.
    title : str
        Force a specific title.
    source : str 
        Force a specific source.

    Returns
    -------
    ParsedDocument
        The parsed document.
    """
    # parse data
    soup = BeautifulSoup(html)
    text = soup.get_text()

    # meta!
    title = title if title else soup.title.string if soup.title else ""

    return parse_text(text, title, source)

#### GETTERS ####
def get_hash(uri:str, context:AgentContext):
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
                                                              {"term": {"user":
                                                                        context.uid}}]}})["hits"]
    if results["total"]["value"] > 0:
        hash = results["hits"][0]["_source"]["hash"]
    return hash

def get_fulltext(hash:str, context:AgentContext):
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
                                                          {"term": {"user":
                                                                    context.uid}}]}},
                                 fields=["text"], size=1)
    hits = [i["fields"]["text"][0] for i in doc["hits"]["hits"]]

    if len(hits) > 0: return hits[0]

def get_nth_chunk(hash, n, context):
    """Read a document possibly stored in the cache by chunk.

    Parameters
    ----------
    hash : str
        The string hash to read.
    n : int
        The nth chunk to read.
    context : AgentContext
        The context pointer to use to perform parsing.

    Return
    ------
    Optional[str]
        str full text, or None.
    """
    res = context.elastic.search(index="simon-paragraphs",
                                query={"bool":
                                        {"must": [
                                            {"term": {"user": context.uid}},
                                            {"term": {"hash": hash}},
                                            {"term": {"metadata.seq": n}},
                                        ]}},
                                fields=["text"],
                                size=1)

    if res["hits"]["total"]["value"] == 0: return None
    res = [i["fields"]["text"][0] for i in res["hits"]["hits"]][0]

    return res

def get_range_chunk(hash, start, end, context):
    """Read a document possibly stored in the cache by chunk.

    Parameters
    ----------
    hash : str
        The string hash to read.
    start : int
        Get chunk starting seq.
    end : int
        Get chunk end seq.
    context : AgentContext
        The context pointer to use to perform parsing.

    Return
    ------
    Optional[List[str]]
        list of results, or None.
    """
    res = context.elastic.search(index="simon-paragraphs",
                                 query={"bool":
                                        {"must": [
                                            {"term": {"user": context.uid}},
                                            {"term": {"hash": hash}},
                                            {"range": {"metadata.seq": {"gte": start,
                                                                        "lte": end}}},
                                        ]}},
                                 fields=["text", "metadata.seq"])

    if res["hits"]["total"]["value"] == 0: return None

    # we get the sequence and re-sort it in case sequences are indexed in an unexpected order
    res = sorted([(i["fields"]["metadata.seq"][0],
                   i["fields"]["text"][0]) for i in res["hits"]["hits"]], key=(lambda x:x[0]))

    return [i[1] for i in res]

def top_tf(hash:str, context:AgentContext, k=3):
    """Retrieve the top n paragraphs of `hash` based on TFIDF 

    Parameters
    ----------
    hash : str
        The document to look for.
    context : AgentContext
        Context pointer to be used for operations.
    k : optional, int
        Number of values to return.

    Return
    ------
    List[str]
        Results of the search.
    """

    # res = context.elastic.search()
    res = context.elastic.search(index="simon-paragraphs",
                                query={"bool": {"must": [{"term": {"hash": hash}},
                                                        {"term": {"user":
                                                                    context.uid}}]}},
                                fields=["text"],
                                sort=[{"metadata.tf": {"order": "desc"}}],
                                size=k)
    return [i["fields"]["text"][0] for i in res["hits"]["hits"]]

def suggest(query:str, context:AgentContext, k=8):
    """string automcomplete to suggest article titles

    Parameters
    ----------
    query : str
        The string hash to read.
    context : AgentContext
        The context pointer to use to perform parsing.
    k : optional, int
        Number of results to return 

    Return
    ------
    List[Tuple[str, str, str]]
        Title, text, hash
    """

    docs = context.elastic.search(index="simon-fulltext",
                                  suggest={"title-suggest": {
                                      "prefix": query,
                                      "completion": {
                                          "field": "metadata.title"
                                      },
                                  }},
                                  query={"bool": {"must": [{"term": {"user":
                                                                     context.uid}}]}})

    options = docs["suggest"]["title-suggest"][0]["options"]

    # filter for matching UIDs and get fields
    matching = [(i["_source"]["metadata"]["title"], i["_source"]["hash"])
                for i in options if i["_source"]["user"] == context.uid]

    return matching

def search(context:AgentContext, queries=[], query:str=None, search_type=IndexClass.CHUNK,
           k=5, threshold=None, tf_threshold=0.3):
    """ElasticSearch the database based on a keyword query!

    Parameters
    ----------
    context : AgentContext
        Context pointer to be used for operations.
    query : str
        The query to ask.
    queries : List[str]
        For associative searches, the queries to ask.
    search_type : IndexClass
        Which index to search. Options include
        IndexClass.CHUNK or IndexClass.FULLTEXT.
    k : optional, int
        Number of values to return.
    threshold : optional, float
        Threshold of score before a value is returned.
    tf_threshold : optional, float
        Threshold of TFIDF before a value is returned,
        if seaching on index CHUNK or KEYWORD.

    Return
    ------
    List[str]
        Results of the search.
    """
    if not threshold and search_type == IndexClass.CHUNK:
        threshold = 0.9
    elif not threshold:
        threshold = 5

    if not queries:
        queries = [query]

    # get results
    squery = {
        "bool": {"must": [
            {"term": {"user": context.uid}},
        ]}
    }

    for query in queries:
        squery["bool"]["must"].append({"match": {"text": query}})

    kquery = []

    if search_type == IndexClass.CHUNK:
        L.debug("BEGIN EMBED")
        for query in queries:
            kquery.append({"field": "embedding",
                           "query_vector": context.embedding.embed_query(query),
                           "k": k,
                           "num_candidates": 50,
                           "filter": [{"term": {"user": context.uid}},
                                      {"match": {"text": query}}]})
        L.debug("END EMBED")

    # if doc_hash:
    #     squery["bool"]["must"].append({"term": {"hash": doc_hash}})

    #     if kquery:
    #         kquery["filter"].append({"term": {"hash": doc_hash}})

    if tf_threshold!=None and search_type != IndexClass.FULLTEXT:
        squery["bool"]["must"].append({"range": {"metadata.tf": {"gte": tf_threshold}}})

        if len(kquery) > 0:
            for i in kquery:
                i["filter"].append({"range": {"metadata.tf": {"gte": tf_threshold}}})

    L.debug("BEGIN SEARCH")
    if search_type == IndexClass.CHUNK:
        results = context.elastic.search(index="simon-paragraphs", knn=kquery, size=str(k))
    elif search_type == IndexClass.FULLTEXT:
        results = context.elastic.search(index="simon-fulltext", query=squery, size=str(k))
    elif search_type == IndexClass.KEYWORDS:
        results = context.elastic.search(index="simon-paragraphs", query=squery, size=str(k))
    L.debug("END SEARCH")

    results = [{"id": i["_id"],
                "text": i["_source"]["text"],
                "metadata": i["_source"]["metadata"],
                "hash": i["_source"]["hash"],
                "score": i["_score"]}
               for i in results["hits"]["hits"] if i["_score"] > threshold]

    return results

def similar(id:str, context:AgentContext, k=5, threshold=0.9) -> List[str]:
    """search for entries with similar meaning around a entry ID

    find the nearest entries across the database to an entry.

    Parameters
    ----------
    id : str
        the ID of the entry to search nearby; NOTE! this is *NOT*
        the hash of the element. It is the ID of the CHUNK. search()
        returns both id (unique to each chunk) and hash (unique to each
        document). Pass this element the ID.
    context : AgentContext
        the context of the agent
    k : int
        number of results to return
    threshold : float
        the float similarity threshold.

    Returns
    -------
    List[str]
        the returned entries
    """
   
    # get results
    squery = {
        "bool": {"must": [
            {"term": {"user": context.uid}},
            {"term": {"_id": id}}
        ]}
    }

    # search for the element with the correct ID
    results = context.elastic.search(index="simon-paragraphs", query=squery, size=1)

    # and raise an exception if we found nothing because the ID is dud
    if len(results["hits"]["hits"]) == 0:
        raise Exception(f"simon: the ID of the chunk provided '{id}' is not found; ensure you are providing an ID from CHUNK or KEYWORD index classes, and that its NOT the *hash* of the chunk. See the docstring of this field for more info.")
    
    embedding = results["hits"]["hits"][0]["_source"]["embedding"]


    # and create the query
    kquery = {"field": "embedding",
              "query_vector": embedding,
              "k": k,
              "num_candidates": 800,
              "filter": [{"term": {"user": context.uid}}]}

    # search again, with the embedding
    # we search k+1 because the top result is just the original element
    results = context.elastic.search(index="simon-paragraphs", knn=kquery, size=str(k+1))

    results = [{"text": i["_source"]["text"],
                "metadata": i["_source"]["metadata"],
                "hash": i["_source"]["hash"],
                "score": i["_score"]}
               for i in results["hits"]["hits"] if i["_score"] > threshold]

    # we drop the top result, because that's the element itself
    return results[1:]

#### DELETERS ####
def delete_document(hash:str, context:AgentContext):
    """Removes an indexed document

    Parameters
    ----------
    hash : str
        The string document to delete
    context : AgentContext
        Information about data stores, etc. which determines
        the context.
    """

    context.elastic.delete_by_query(index="simon-fulltext",
                                    query={"bool": {"must": [{"term": {"hash": hash}},
                                                         {"term": {"user":
                                                                   context.uid}}]}})

    context.elastic.delete_by_query(index="simon-paragraphs",
                                    query={"bool": {"must": [{"term": {"hash": hash}},
                                                         {"term": {"user":
                                                                   context.uid}}]}})

    context.elastic.delete_by_query(index="simon-cache",
                                    query={"bool": {"must": [{"term": {"hash": hash}},
                                                         {"term": {"user":
                                                                   context.uid}}]}})


    context.elastic.indices.refresh(index="simon-fulltext")
    context.elastic.indices.refresh(index="simon-paragraphs")
    context.elastic.indices.refresh(index="simon-cache")


#### SETTERS ####
def bulk_index(documents:List[ParsedDocument], context:AgentContext):
    assert len(documents) > 0, "we can't index 0 documents"

    L.info(f"Bulk indexing {len(documents)} documents...")

    # get the hashes from the documents
    hashes = [i.hash for i in documents]

    # and search through for those hashes
    prefetch = []

    L.debug(f"Identifying already indexed documents...")
    # we do prefetch.append({"index": "simon-paragraphs"}) because every paragraph
    # requires a new index note
    for indx, hash in enumerate(hashes):
        prefetch.append({"index": "simon-fulltext"})
        prefetch.append({
            "query": {
                "bool": {
                    "must": [
                        {"term": {"hash": hash}},
                        {"term": {"user": context.uid}}
                    ],
                }},
            "size": 1
        })

    request = ""

    for i in prefetch:
        request += f"{json.dumps(i)} \n"

    success = False

    while not success:
        try:
            prefetch = context.elastic.msearch(searches=request)["responses"]
            success = True
        except:
            pass

    # filter the input documents by those that aren't previously indexed
    not_found = [not bool(i["hits"]["total"]["value"]) for i in prefetch]

    if sum(not_found) == 0:
        L.debug(f"All of {len(documents)} documents are all indexed. Returning...")
        return

    # documents to index
    _, filtered_documents = zip(*filter(lambda x:x[0], zip(not_found, documents)))

    # remove duplicates
    filtered_documents = list(set(filtered_documents))

    L.debug(f"Total of {len(filtered_documents)} documents remain to truly index.")

    L.debug(f"TFIDF analyzing {len(filtered_documents)} documents...")

    # calculate tfidf for use later
    tfs = []

    for doc in filtered_documents:
        try:
            vectorizer = TfidfVectorizer()
            X = vectorizer.fit_transform(doc.paragraphs)
            tf_sum = X.sum(1).squeeze().tolist()[0]
            tfs.append(tf_sum)
        except ValueError:
            L.warning(f"Found document with no analyzable content: {doc.paragraphs}.")
            tfs.append([0 for _ in doc.paragraphs])

    # calculate the documents to embed and chunks to update
    embed_text = []
    updates = []

    L.debug(f"calculating chunk for {len(filtered_documents)} documents...")
    # We now go through each of the paragraphs. Index if needed, update the hash
    # if we already have the paragraph.
    for i, doc in enumerate(filtered_documents):
        tf_vec = tfs[i]

        for indx, (tf, paragraph) in enumerate(zip(tf_vec, doc.paragraphs)):
            # check if the we already have the element indexed
            embed_text.append((doc.meta.get("title", "")
                                if doc.meta.get("title", "") else "")+": "+paragraph.strip())

            updates.append({"user": context.uid,
                            "metadata": {"title": doc.meta.get("title"),
                                        "source": doc.meta.get("source"),
                                        "seq": indx,
                                        "tf": tf,
                                        "total": len(doc.paragraphs)},
                            "hash": doc.hash,
                            "text": paragraph,
                            "_op_type": "index",
                            "_index": "simon-paragraphs"})

    # create embeddings in bulk
    L.debug(f"embedding {len(embed_text)} chunks...")
    embeddings = context.embedding.embed_documents(embed_text)

    # slice the embeddings in
    for i, em in zip(updates, embeddings):
        i["embedding"] = em

    L.debug(f"calculating full text updates for {len(filtered_documents)} documents...")
    # create the document-level updates
    for doc in filtered_documents:
        updates.append({"user": context.uid,
                        "metadata": {"title": doc.meta.get("title"),
                                    "source": doc.meta.get("source")},
                        "hash": doc.hash,
                        "text": doc.main_document,
                        "_op_type": "index",
                        "_index": "simon-fulltext"})

    L.debug(f"submitting {len(filtered_documents)} documents to the index...")
    # and bulk!
    bulk(context.elastic, updates)

    # refresh indicies
    context.elastic.indices.refresh(index="simon-fulltext")
    context.elastic.indices.refresh(index="simon-paragraphs")
    L.debug(f"Done with indexing {len(documents)} documents; {len(filtered_documents)} actually indexed; rest cached.")





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

    L.info(f"Indexing {doc.hash}...")
    # try to cache the old cache
    old_hash = None

    # And check if we have already indexed the doc
    indicies = context.elastic.search(index="simon-fulltext",
                                      query={"bool": {"must": [{"term": {"hash": doc.hash}},
                                                               {"term": {"user":
                                                                         context.uid}}]}})["hits"]
    # If not, do so!
    if indicies["total"]["value"] == 0:
        # change detected, remove elements of the same title
        L.debug(f"Detecting historical versions {doc.hash}...")
        title = doc.meta.get("title", "")
        if title and title != "":
            titles = context.elastic.search(index="simon-fulltext",
                                            query={"bool": {"must": [{"term": {"metadata.title": title.lower()}},
                                                                     {"term": {"user":
                                                                               context.uid}}]}})

            # remove the previous versions that we found
            for result in titles["hits"]["hits"]:
                old_hash = result["_source"]["hash"]
                context.elastic.delete(index="simon-fulltext", id=result["_id"])

            # [delete_document(doc["_source"]["hash"], context) for doc in titles["hits"]["hits"]]

        L.debug(f"Fulltext indexing {doc.hash}...")
        context.elastic.index(index="simon-fulltext",
                              document={"user": context.uid,
                                        "metadata": {"title": doc.meta.get("title"),
                                                     "source": doc.meta.get("source")},
                                        "hash": doc.hash,
                                        "text": doc.main_document})
    else:
        L.debug(f"{doc.hash} is already indexed, skipping...")
        return # if we have already indexed this, just leave

    L.debug(f"TFIDF analyzing {doc.hash}...")

    # calculate tfidf for use later
    vectorizer = TfidfVectorizer()
    try:
        X = vectorizer.fit_transform(doc.paragraphs)
        tf_sum = X.sum(1).squeeze().tolist()[0]
    except ValueError:
        L.info(f"Found document with no analyzable content: {doc.paragraphs}.")
        context.elastic.indices.refresh(index="simon-paragraphs")
        return

    documents = []
    updates = []
    prefetch = []


    L.debug(f"Chuck analyzing {doc.hash}...")
    # we do prefetch.append({"index": "simon-paragraphs"}) because every paragraph
    # requires a new index note
    for indx, paragraph in enumerate(doc.paragraphs):
        prefetch.append({"index": "simon-paragraphs"})
        prefetch.append({
            "query": {
                "bool": {
                    "must": [
                        {"match": {"text": paragraph}},
                        {"term": {"user": context.uid}}
                    ],
                }},
            "size": 1
        })

    request = ""

    for i in prefetch:
        request += f"{json.dumps(i)} \n"

    success = False

    while not success:
        try:
            prefetch = context.elastic.msearch(body=request)["responses"]
            success = True
        except:
            pass

    L.debug(f"Chunk patching {doc.hash}...")
    # We now go through each of the paragraphs. Index if needed, update the hash
    # if we already have the paragraph.
    for indx, (paragraph, indicies) in enumerate(zip(doc.paragraphs, prefetch)):
        # check if the we already have the element indexed

        indicies = indicies["hits"]
        tf = tf_sum[indx]

        # if so, just update their hashes
        if len(indicies["hits"]) > 0 and indicies["hits"][0]["_source"]["text"] == paragraph:
            context.elastic.update(index="simon-paragraphs", id=indicies["hits"][0]["_id"],
                                   body={"doc": {"hash": doc.hash,
                                                 "metadata.tf": tf}})
        # if not, write it down for bulk operations
        else:
            documents.append((doc.meta.get("title", "")
                              if doc.meta.get("title", "") else "")+": "+paragraph.strip())

            updates.append({"user": context.uid,
                            "metadata": {"title": doc.meta.get("title"),
                                         "source": doc.meta.get("source"),
                                         "seq": indx,
                                         "tf": tf,
                                         "total": len(doc.paragraphs)},
                            "hash": doc.hash,
                            "text": paragraph,
                            "_op_type": "index",
                            "_index": "simon-paragraphs"})

    # create embeddings in bulk
    L.debug(f"embedding {len(documents)} documents...")
    embeddings = context.embedding.embed_documents(documents)

    # slice the embeddings in
    for i, em in zip(updates, embeddings):
        i["embedding"] = em

    L.debug(f"submittig {doc.hash}...")
    # and bulk!
    bulk(context.elastic, updates)

    # refresh indicies
    context.elastic.indices.refresh(index="simon-fulltext")
    context.elastic.indices.refresh(index="simon-paragraphs")

    # if an old hash was detected, we delete any traces of the old document
    if old_hash:
        delete_document(old_hash, context)
    L.debug(f"Done analyzing {doc.hash}...")

#### GLUE ####
# A function to assemble CHUNK-type search results

def assemble_chunks(results, context, padding=1):
    """Assemble CHUNK type results into a string

    Parameters
    ----------
    results : str
        Output of search().
    context : AgentContext
        Context to use.
    padding : optional,int
        The context padding to provide the model.
        
    Return
    ------
    List[Tuple[float, str, str]]
        A list of score, title, range.
    """


    # otherwise it'd be empty!
    if len(results) == 0:
        return ""

    # group by source, parsing each one at a time
    groups = groupby(sorted(results, key=lambda x:x.get("hash")),
                     lambda x:x.get("hash"))
    stitched_ranges = []

    for _, group in groups:
        # get the context groups
        group = sorted(group, key=lambda x:x.get("metadata", {}).get("seq", 10000))
        total = group[0].get("metadata", {}).get("total", 10000)
        title = group[0].get("metadata", {}).get("title", "")
        source = group[0].get("metadata", {}).get("source", "")
        hash = group[0].get("hash", "")
        mean_score = sum([i.get("score", 0) for i in group])/len(group)

        # generate the chunk regions
        chunks = [(max(0, i.get("metadata", {}).get("seq", 0)-padding),
                min(total, i.get("metadata", {}).get("seq", 10000)+padding))
                for i in group]
        # smooth out overlapping chunks (if two chunks overlap, we create a bigger one
        # encompassing both)
        smooth_chunks = []
        # if the current ending is after the next starting, we take
        # the next ending chunk instead
        start, end = chunks.pop(0)
        while len(chunks) != 0:
            new_start, new_end = chunks.pop(0)

            if end <= new_start:
                smooth_chunks.append((start, end))
                start = new_start
                end = new_end
            else:
                end = max(end, new_end)
        smooth_chunks.append((start, end))
        # now, get these actual chunks + stich them together with "..."
        range_text = "\n\n...\n\n".join(["\n".join(get_range_chunk(hash, i,j, context))
                                for i,j in smooth_chunks])
        # metadat
        stitched_ranges.append((mean_score, title, range_text, source, hash))

    stitched_ranges = sorted(stitched_ranges, key=lambda x:x[0], reverse=True)

    # and now, assemble everything with slashes between and return
    return stitched_ranges

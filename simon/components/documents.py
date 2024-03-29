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

from collections import defaultdict
from psycopg2.extras import execute_values

import logging
L = logging.getLogger("simon")

# Networking
import requests

# langchain stuff
from langchain.embeddings.base import Embeddings

# nltk
from ..utils.helpers import sent_tokenize_d

# tika
from tika import parser

# soup
from bs4 import BeautifulSoup

# TFIDF
from sklearn.feature_extraction.text import TfidfVectorizer

# decorator business
from functools import wraps

# utilities
import json

from ..models import *

from psycopg2.errors import InFailedSqlTransaction, UndefinedTable

# Wrapper function to provide database safety (caching db errors
# or warning about undefined table)
def dbsafe(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        try: 
            return f(*args, **kwds)
        except (InFailedSqlTransaction, UndefinedTable) as e:
            # try to get the context from the function
            context = kwds.get("context")
            if not context:
                for i in args:
                    if type(i) == AgentContext:
                        context = i

            # try to retry any failed transactions
            if type(e) == InFailedSqlTransaction:
                L.debug("The previous SQL command failed, retrying...")
                if context:
                    context.cnx.rollback()
                    return wrapper(*args, **kwds)
                else:
                    raise RuntimeError("A previous SQL command failed, and Simon was unable to roll the transaction back.\nHint: set up a new copy of AgentContext with a fresh psql connection by restarting your Python session or by call `simon.create_context` again.")
            # tell the user to initialize the database
            elif type(e) == UndefinedTable:
                raise ValueError("The database we are provided has not been initialized.\nHint: call `simon.setup(context)` to set up the tables needed for Simon. You only have to do this once per new psql database you use.")
    return wrapper



#### SANITIZERS ####
def __chunk(text):

    sentences = sent_tokenize_d(text)
     
    # makes groups of 5 sentences, joined, as the chunks
    parsed_chunks = [re.sub(r" +", " "," ".join(sentences[i:i+3]).strip()).strip()
                        for i in range(0, len(sentences), 3)]
    # then, find paragraphs
    parsed_chunks = [j for i in parsed_chunks for j in i.split("\n\n")]

    # and also create the bigger document
    parsed_text = "\n".join(parsed_chunks)
    # hash the text
    hash = hashlib.sha256(parsed_text.encode()).hexdigest()

    return parsed_chunks, parsed_text, hash

#### PARSERS ####
def parse_text(text, title=None, source=None) -> ParsedDocument:
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
    parsed_chunks, parsed_text, hash = __chunk(text)

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

    paragraphs = [i.strip() for i in soup.get_text().split("\n")
                  if i.strip() != ""]

    # deduplicate
    # we do this dictionary dedplication instead of list(set()) to preserve order
    seen = {}
    paragraphs = [seen.setdefault(i, i) for i in paragraphs if i not in seen]

    # get title
    title = title if title else soup.title.string if soup.title else ""

    # return!
    return ParsedDocument(" ".join(paragraphs), paragraphs, {
        "source": source,
        "title": title
    })


#### GETTERS ####
@dbsafe
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

    cur = context.cnx.cursor()

    cur.execute("SELECT hash FROM simon_cache WHERE uri = %s AND uid = %s LIMIT 1;", (uri, context.uid))
    res = cur.fetchone()

    if not res:
        return

    result = res[0]
    cur.close()

    return result

@dbsafe
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

    cur = context.cnx.cursor()

    cur.execute("SELECT text FROM simon_fulltext WHERE hash = %s AND uid = %s LIMIT 1;", (hash, context.uid))
    res = cur.fetchone()

    if not res:
        return

    result = res[0]
    cur.close()

    return result

@dbsafe
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

    cur = context.cnx.cursor()

    cur.execute("SELECT text FROM simon_paragraphs WHERE hash = %s AND uid = %s AND seq = %s LIMIT 1;", (hash, context.uid, n))
    res = cur.fetchone()

    if not res:
        return

    result = res[0]
    cur.close()

    return result

@dbsafe
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

    cur = context.cnx.cursor()

    cur.execute("SELECT text FROM simon_paragraphs WHERE hash = %s AND uid = %s AND seq >= %s AND seq <= %s ORDER BY seq;",
                (hash, context.uid, start, end))

    res = cur.fetchall()

    result = [i[0] for i in res]
    cur.close()

    return result

@dbsafe
def get_range_chunks(queries, context):
    """Read a group of documents possibly stored in the cache by chunk.

    Parameters
    ----------
    queries: List[Tuple[str, int, int]]
        [(hash, start, end), ...]
    context : AgentContext
        The context pointer to use to perform parsing.

    Return
    ------
    Optional[List[str]]
        list of results, or None.
    """

    cur = context.cnx.cursor()

    cur = context.cnx.cursor()
    sqls = [cur.mogrify("(SELECT text,hash FROM simon_paragraphs WHERE hash = %s AND uid = %s AND seq >= %s AND seq <= %s ORDER BY seq)", (hash, context.uid, start, end))
            for (hash, start, end) in queries]

    cur.execute(b" UNION ".join(sqls)+b";")
    res = cur.fetchall()

    data = defaultdict(list)
    for (text, hash) in res:
        data[hash].append(text)
    cur.close()

    return dict(data)

@dbsafe
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


    cur = context.cnx.cursor()

    cur.execute("SELECT text FROM simon_paragraphs WHERE hash = %s AND uid = %s ORDER BY tf DESC LIMIT %s;", (hash, context.uid, k))
    res = cur.fetchall()

    result = [i[0] for i in res]
    cur.close()

    return result

@dbsafe
def autocomplete(query:str, context:AgentContext, k=8):
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

    cur = context.cnx.cursor()

    cur.execute("SELECT title FROM simon_paragraphs WHERE uid = %s AND LOWER( title ) LIKE %s LIMIT %s;", (context.uid, query.lower()+"%", k))
    res = cur.fetchall()

    result = [i[0] for i in res]
    cur.close()

    return result

@dbsafe
def search(context:AgentContext, queries=[], query:str=None, search_type=IndexClass.CHUNK, k=5, tf_threshold=1.5):
    """search the database based on a query!

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
    tf_threshold : optional, float
        The TFIDF threshold.

    Return
    ------
    List[str]
        Results of the search.
    """

    if not queries:
        queries = [query]

    # calculate result to return per query
    # becasue we do each search seperately
    k = (k//len(queries))+1

    L.debug(f"fufilling search request for {queries}...")

    requests = []
    embeddings = []

    query_base = "SET LOCAL ivfflat.probes = 20; SELECT text, hash, src, title, tf, seq, total FROM simon_paragraphs "

    L.debug(f"building queries for {queries}...")
    if search_type==IndexClass.FULLTEXT:
        for _ in range(len(queries)):
            requests.append(query_base+"WHERE uid = %s AND TF > %s AND text_fuzzy @@ plainto_tsquery('english', %s) LIMIT %s;")
    elif search_type==IndexClass.CHUNK:
        for _ in range(len(queries)):
            requests.append(query_base+"WHERE uid = %s AND TF > %s ORDER BY embedding <#> %s LIMIT %s;")

        L.debug(f"building embeddings for {queries}...")
        embeddings = [context.embedding.embed_query(q) for q in queries]

    results = []

    L.debug(f"executing {queries}...")
    cur = context.cnx.cursor()

    for indx, querystring in enumerate(requests):
        cur.execute(querystring, (context.uid, tf_threshold, queries[indx] if search_type==IndexClass.FULLTEXT else str(embeddings[indx]), k))
        results += cur.fetchall()

    L.debug(f"assembling results for {queries}...")
    results = [{
        "text": text,
        "hash": hash,
        "metadata": {
            "title": title,
            "source": src,
            "tf": tf,
            "seq": seq,
            "total": total,
        }
    } for (text, hash, src, title, tf, seq, total) in results]

    L.debug(f"done with {queries}...")
    cur.close()
    return results

#### DELETERS ####
@dbsafe
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

    cur = context.cnx.cursor()

    cur.execute("DELETE FROM simon_paragraphs WHERE uid = %s AND hash = %s;", (context.uid, hash))
    cur.execute("DELETE FROM simon_fulltext WHERE uid = %s AND hash = %s;", (context.uid, hash))
    cur.execute("DELETE FROM simon_cache WHERE uid = %s AND hash = %s;", (context.uid, hash))

    context.cnx.commit()
    cur.close()

#### SETTERS ####
@dbsafe
def bulk_index(documents:List[ParsedDocument], context:AgentContext):
    assert len(documents) > 0, "we can't index 0 documents"

    L.info(f"Bulk indexing {len(documents)} documents...")

    # get the hashes from the documents
    hashes = [i.hash for i in documents]

    # and search through for those hashes
    prefetch = []

    L.debug(f"Identifying already indexed documents...")
    cur = context.cnx.cursor()
    sqls = [cur.mogrify("SELECT hash FROM simon_fulltext WHERE hash = %s AND uid = %s LIMIT 1;", (hash, context.uid))
            for hash in hashes]
    cur.execute(b";".join(sqls))
    res = cur.fetchall()
    res = [i[0] for i in res]

    # for hash in hashes:
                             
    #     cur.execute("SELECT hash FROM simon_fulltext WHERE hash = %s AND uid = %s LIMIT 1;", (hash, context.uid))
    #     res = cur.fetchone()
    #     prefetch.append(res)

    # documents to index
    filtered_documents = list(filter(lambda x:x.hash not in res, documents))

    if len(filtered_documents) == 0:
        L.debug(f"All of {len(res)} documents are all indexed. Returning...")
        return

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

    L.debug(f"calculating chunk-level updates for {len(filtered_documents)} documents...")
    # We now go through each of the paragraphs. Index if needed, update the hash
    # if we already have the paragraph.
    for i, doc in enumerate(filtered_documents):
        tf_vec = tfs[i]

        for indx, (tf, paragraph) in enumerate(zip(tf_vec, doc.paragraphs)):
            # check if the we already have the element indexed
            embed_text.append((doc.meta.get("title", "")
                                if doc.meta.get("title", "") else "")+": "+paragraph.strip())

            updates.append([doc.hash, context.uid, paragraph, None, doc.meta.get("source", ""),
                            doc.meta.get("title", ""), tf, indx, len(doc.paragraphs)])

    # create embeddings in bulk
    L.debug(f"embedding {len(embed_text)} chunks...")
    embeddings = []

    for i in range(0, len(embed_text), 16):
        chunk = embed_text[i:i+16]
        embeddings += context.embedding.embed_documents(chunk)

    # slice the embeddings in
    for i, em in zip(updates, embeddings):
        i[3] = em

    # perform the updates
    L.debug(f"submitting {len(filtered_documents)} documents to the chunk-level index...")
    execute_values (
        cur, "INSERT INTO simon_paragraphs (hash, uid, text, embedding, src, title, tf, seq, total) VALUES %s;",
        updates
    )

    updates = []
    L.debug(f"calculating fulltext-level updates for {len(filtered_documents)} documents...")
    # create the document-level updates
    for doc in filtered_documents:
        updates.append((doc.hash, context.uid, doc.main_document, doc.meta.get("source", ""),
                        doc.meta.get("title", "")))

    L.debug(f"submitting {len(filtered_documents)} documents to the document-level index...")
    execute_values (
        cur, "INSERT INTO simon_fulltext (hash, uid, text, src, title) VALUES %s;",
        updates
    )

    # refresh indicies
    L.debug(f"committing changes for {len(filtered_documents)}...")
    context.cnx.commit()

    L.debug(f"Done with indexing {len(documents)} documents; {len(filtered_documents)} actually indexed; rest cached.")

    cur.close()

@dbsafe
def index_document(doc:ParsedDocument, context:AgentContext):
    """Indexes a document, if needed.

    Parameters
    ----------
    doc : ParsedDocument
        Document to Index.
    context : AgentContext
        Information about data stores, etc. which determines
        the context.
    """

    L.info(f"Indexing {doc.hash}...")
    bulk_index([doc], context)

    # lol

@dbsafe
def cache(uri:str, hash:str, context:AgentContext):
    """cache a document to prevent future fetches

    Parameters
    ----------
    uri : str
        url to cache from
    hash : str
        hash to cache
    context : AgentContext
        the agent context to cache with
    """
    

    cur = context.cnx.cursor()

    cur.execute("INSERT INTO simon_cache (uri, hash, uid) VALUES (%s, %s, %s);", (uri, hash, context.uid))

    context.cnx.commit()
    cur.close()


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

    # keep the original order of hashes
    # we do this dictionary dedplication instead of list(set()) to preserve order
    seen = {}
    hashes = [seen.setdefault(x["hash"], x["hash"]) for x in results if x["hash"] not in seen]

    # group by source, parsing each one at a time
    groups = groupby(sorted(results, key=lambda x:x.get("hash")),
                     lambda x:x.get("hash"))
    stitched_ranges = []
    to_fetch = []

    for _, group in groups:
        # get the context groups
        group = sorted(group, key=lambda x:x.get("metadata", {}).get("seq", 10000))
        total = group[0].get("metadata", {}).get("total", 10000)
        title = group[0].get("metadata", {}).get("title", "")
        source = group[0].get("metadata", {}).get("source", "")
        hash = group[0].get("hash", "")

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
                to_fetch.append((hash, start, end))
                start = new_start
                end = new_end
            else:
                end = max(end, new_end)
        to_fetch.append((hash, start, end))
        # now, get these actual chunks + stich them together with "..."
        # metadat
        stitched_ranges.append([title, None, source, hash])


    # fetch the text
    chunks = get_range_chunks(to_fetch, context)

    # iterate through the data
    for res in stitched_ranges:
        hash = res[-1]
        chunk_data = chunks[hash]
        res[1] = "\n".join(chunk_data)

    # reorder the results based on the original ranking
    ordered_results = []
    for hash in hashes:
        ordered_results += [i for i in stitched_ranges if i[3] == hash]
        

    # range_text = "\n\n...\n\n".join(["\n".join(get_range_chunk(hash, i,j, context))
    #                         for i,j in smooth_chunks])

    # stitched_ranges = sorted(stitched_ranges, key=lambda x:x[0], reverse=True)

    # and now, assemble everything with slashes between and return
    return ordered_results

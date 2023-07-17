"""
documents.py
Components for document parsing.
"""

# System Library
import os
import time
import hashlib
import mimetypes
from typing import List
from itertools import groupby, islice
from tempfile import TemporaryDirectory

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

from tqdm import tqdm

# utilities
from ..utils.elastic import *
from ..models import *

#### SANITIZERS ####
def __chunk(text, delim="\n\n"):
    # if there are no delimters, we do a dumb thing:
    if delim not in text:
        sentences = sent_tokenize(text)
        # makes groups of 5 sentences, joined, as the chunks
        parsed_chunks = [" ".join(sentences[i:i+5]).strip()
                         for i in range(0, len(sentences), 5)]
    else:
        # clean the chunks
        parsed_chunks = [i.replace("\n"," ").replace("  ", " ").strip()
                     for i in text.split(delim) if i != '']

    # if any chunk is longer than 8*2048=10240 characters long (>2048 words, i.e. 1/2 4097)
    # we use the chunking technique 
    if sum([len(i)>2048 for i in parsed_chunks]) > 0:
        sentences = sent_tokenize(text)
        # makes groups of 5 sentences, joined, as the chunks
        parsed_chunks = [" ".join(sentences[i:i+5]).strip()
                            for i in range(0, len(sentences), 5)]
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
    return ParsedDocument(parsed_text, parsed_chunks, hash, meta)

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
                                  }})

    options = docs["suggest"]["title-suggest"][0]["options"]

    # filter for matching UIDs and get fields
    matching = [(i["_source"]["metadata"]["title"], i["_source"]["text"],
                 i["_source"]["hash"])
                for i in options if i["_source"]["user"] == context.uid]

    return matching

def search(query:str, context:AgentContext, search_type=IndexClass.CHUNK,
           doc_hash=None, k=5, threshold=None, tf_threshold=0.3):
    """ElasticSearch the database based on a keyword query!

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

    # get results
    squery = {
        "bool": {"must": [
            {"term": {"user": context.uid}},
            {"match": {"text": query}}
        ]}
    }

    kquery = None

    if search_type == IndexClass.CHUNK:
        kquery = {"field": "embedding",
                "query_vector": context.embedding.embed_query(query),
                "k": k,
                "num_candidates": 800,
                "filter": [{"term": {"user": context.uid}}]}

    if doc_hash:
        squery["bool"]["must"].append({"term": {"hash": doc_hash}})

        if kquery:
            kquery["filter"].append({"term": {"hash": doc_hash}})

    if tf_threshold!=None and search_type != IndexClass.FULLTEXT:
        squery["bool"]["must"].append({"range": {"metadata.tf": {"gte": tf_threshold}}})

        if kquery:
            kquery["filter"].append({"range": {"metadata.tf": {"gte": tf_threshold}}})

    if search_type == IndexClass.CHUNK:
        results = context.elastic.search(index="simon-paragraphs", knn=kquery, size=str(k))
    elif search_type == IndexClass.FULLTEXT:
        results = context.elastic.search(index="simon-fulltext", query=squery, size=str(k))
    elif search_type == IndexClass.KEYWORDS:
        results = context.elastic.search(index="simon-paragraphs", query=squery, size=str(k))

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
 at   Why is this code so agressive about search/checking first
    before indexing? Because indexing is SIGNIFICANTLY more
    expensive in Elastic than reading. Because its a search db
    after all.
    """

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

        context.elastic.index(index="simon-fulltext",
                              document={"user": context.uid,
                                        "metadata": {"title": doc.meta.get("title"),
                                                     "source": doc.meta.get("source")},
                                        "hash": doc.hash,
                                        "text": doc.main_document})
    else: return # if we have already indexed this, just leave

    # calculate tfidf for use later
    vectorizer = TfidfVectorizer()
    try:
        X = vectorizer.fit_transform(doc.paragraphs)
        tf_sum = X.sum(1).squeeze().tolist()[0]
    except ValueError:
        print(f"Simon: Found document with no analyzable content: {doc.paragraphs}. Skipping...")
        context.elastic.indices.refresh(index="simon-paragraphs")
        return

    # We now go through each of the paragraphs. Index if needed, update the hash
    # if we already have the paragraph.
    for indx, paragraph in enumerate(tqdm(doc.paragraphs)):
        # check if the we already have the element indexed

        indicies = context.elastic.search(index="simon-paragraphs",
                                          query={"bool": {"must": [{"match": {"text": paragraph}},
                                                                   {"term": {"user":
                                                                             context.uid}}]}},
                                          size=1)["hits"]
        tf = tf_sum[indx]

        # if so, just update their hashes
        if len(indicies["hits"]) > 0 and indicies["hits"][0]["_source"]["text"] == paragraph:
            context.elastic.update(index="simon-paragraphs", id=indicies["hits"][0]["_id"],
                                   body={"doc": {"hash": doc.hash,
                                                 "metadata.tf": tf}})
        else:
            context.elastic.index(index="simon-paragraphs",
                                  document={"user": context.uid,
                                            "metadata": {"title": doc.meta.get("title"),
                                                         "source": doc.meta.get("source"),
                                                         "seq": indx,
                                                         "tf": tf,
                                                         "total": len(doc.paragraphs)},
                                            "hash": doc.hash,
                                            "text": paragraph,
                                            "embedding": context.embedding.embed_documents([(doc.meta.get("title", "") if doc.meta.get("title", "") else "")+": "+paragraph.strip()])[0]})
    # refresh indicies
    context.elastic.indices.refresh(index="simon-fulltext")
    context.elastic.indices.refresh(index="simon-paragraphs")

    # if an old hash was detected, we delete any traces of the old document
    if old_hash:
        delete_document(old_hash, context)
        
#### SPECIAL SETTERS ####

### Read Remote Helpers ###
# These helpers should take a URL, and return an
# object of class ParsedDocument
def __read_remote_helper__DOCUMENT(r, url):
    # Retrieve and parse the document
    with TemporaryDirectory() as tmpdir:
        f = os.path.join(tmpdir, f"simon-cache-{time.time()}")
        with open(f, 'wb') as fp:
            fp.write(r.content)
            doc = parse_tika(f, source=url)
            hash = doc.hash

    return doc

def __read_remote_helper__WEBPAGE(r, url):
    # parse!
    doc = parse_web(r.content, source=url)
    hash = doc.hash

    return doc

### Read Remote Function ###
def read_remote(url:str, context:AgentContext):
    """Read and index a remote file into Elastic.

    Note
    ----
    This function is useful for single FILES/WEB PAGES. Filled with TEXT. For DATA,
    use `ingest_remote`
    

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
    hash = get_hash(url, context)

    # If there is no cache retrieve the doc
    if not hash:
        headers = {'user-agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        content_type = r.headers['content-type'].split(";")[0].strip()

        if "text" in content_type:
            doc = __read_remote_helper__WEBPAGE(r, url)
        elif "application" in content_type:
            doc = __read_remote_helper__DOCUMENT(r, url)
        elif "image" in content_type:
            doc = __read_remote_helper__DOCUMENT(r, url)

        # read hash off of the doc
        hash = doc.hash

        # and pop it into the cache and index
        context.elastic.index(index="simon-cache", document={"uri": url, "hash": hash,
                                                             "user": context.uid})
        context.elastic.indices.refresh(index="simon-cache")
        index_document(doc, context)

    # retrun hash
    return hash

### Ingest Remote Helpers ###
# These helpers should take a URL, and return an
# array of flat dictionaries with flat data fields.
# Like [ {"this": 1, "that": "two"}, {"what": 1, "the": "hell"} ]
def __ingest_remote_helper__JSON(url):
    # download page
    headers = {'user-agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)

    return r.json()

### Ingest Remote Function ###
def ingest_remote(url, context:AgentContext, type:DataType, mappings:Mapping, delim="\n"):
    """Read and index a remote resource into Elastic with a field mapping

    Note
    ----
    This function is useful for STRUCTURED DATA. For SINGLE FILES/PAGES,
    use `ingest_remote`


    Parameters
    ----------
    url : str
        URL to read.
    context : AgentContext
        Context to use.
    type : DataType
        What are we indexing?? JSON? SQL?
    mappings : Mapping
        Which fields match with what index? 
    delim : optional, str
        How do we deliminate chunks? Perhaps smarter in the future but
        for now we are just splitting by a character.
    
    Return
    ------
    List[str]
        List of hashes of the data we have read
    """

    # check mappings
    mappings.check()

    # get the data with the right parser
    if type == DataType.JSON:
        data = __ingest_remote_helper__JSON(url)

    # create documents
    docs = [parse_text(**{map.dest.value:i[map.src] for map in mappings.mappings},
                    delim=delim)
            for i in data]
    # filter for those that are indexed
    docs = list(filter(lambda x:(get_fulltext(x.hash, context)==None), docs))

    # pop each into the index
    # and pop each into the cache and index
    from tqdm import tqdm
    for i in tqdm(docs):
        index_document(i, context)
        source = i.meta.get("source")
        if source and source.strip() != "":
            # remove docs surrounding old hash 
            oldhash = get_hash(source, context)
            if oldhash:
                delete_document(oldhash, context)
            # index new one
            context.elastic.index(index="simon-cache", document={"uri": source, "hash": i.hash,
                                                                 "user": context.uid})
    # refresh
    context.elastic.indices.refresh(index="simon-cache")

    # return hashes
    return [i.hash for i in docs]


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
        stitched_ranges.append((mean_score, title, range_text))

    stitched_ranges = sorted(stitched_ranges, key=lambda x:x[0], reverse=True)

    # and now, assemble everything with slashes between and return
    return stitched_ranges

# context = ""
# hash = read_remote("https://arxiv.org/pdf/1706.03762.pdf", context)
# delete_document(hash, context)


# hash = read_remote("https://arxiv.org/pdf/2004.07606.pdf", context)
# top_tf(hash, context)
# # hash

# results = search("what's a linear map?", context, k=3)
# print(assemble_chunks(results, context))

# ingest_remote("https://www.jemoka.com/index.json",
#               context,
#               DataType.JSON,
#               JSONMapping([StringMappingField("permalink", MappingTarget.SOURCE),
#                            StringMappingField("contents", MappingTarget.TEXT),
#                            StringMappingField("title", MappingTarget.TITLE)]))
              


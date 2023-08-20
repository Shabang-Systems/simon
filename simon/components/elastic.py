from elasticsearch import Elasticsearch

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
                                                                    "hash": {"type": "keyword"},
                                                                    "user": {"type": "keyword"}}})
    es.indices.create(index="simon-fulltext", mappings={"properties": {"hash": {"type": "keyword"},
                                                                       "metadata.source": {"type": "text"},
                                                                       "metadata.title": {"type": "completion"},
                                                                       "text": {"type": "text"},
                                                                       "user": {"type": "keyword"}}})
    es.indices.create(index="simon-paragraphs", mappings={"properties": {"hash": {"type": "keyword"},
                                                                         "metadata.source": {"type": "text"},
                                                                         "metadata.title": {"type": "completion"},
                                                                         # paragraph number (seq / total)
                                                                         "metadata.seq": {"type": "unsigned_long"},
                                                                         "metadata.tf": {"type": "float"},
                                                                         "metadata.total": {"type": "unsigned_long"},
                                                                         "text": {"type": "text"},
                                                                         "embedding": {"type": "dense_vector",
                                                                                       "dims": 1536,
                                                                                       "similarity": "dot_product",
                                                                                       "index": "true"},
                                                                         "user": {"type": "keyword"}}})
    es.indices.create(index="simon-kv", mappings={"properties": {"key": {"type": "keyword"},
                                                                 "value": {"type": "text"},
                                                                 "user": {"type": "keyword"}}})

def _nuke_schema(es:Elasticsearch):
    """Gets rid of everything.

    Parameters
    ----------
    es : Elasticsearch
        Elastic search instance used to store the data.
    """

    if es.indices.exists(index="simon-cache"):
        es.indices.delete(index="simon-cache")
    if es.indices.exists(index="simon-kv"):
        es.indices.delete(index="simon-kv")
    if es.indices.exists(index="simon-fulltext"):
        es.indices.delete(index="simon-fulltext")
    if es.indices.exists(index="simon-paragraphs"):
        es.indices.delete(index="simon-paragraphs")

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
                                                           {"term": {"user": user}}]}}, size=1)
    if len(results["hits"]["hits"]) == 0:
        return (None,None) if return_id else None

    result = results["hits"]["hits"][0]

    if return_id: return result["_source"]["value"], result["_id"]
    else: return result["_source"]["value"]

def kv_getall(es:Elasticsearch, user:str):
    """Get all key-value store

    Parameters
    ----------
    es : Elasticsearch
        The Elastic Instance
    user : str
        UID

    Return
    ------
    Dict
        All kv info on that user
    """


    results = es.search(index="simon-kv", query={"bool":
                                                 {"must": [{"term": {"user": user}}]}},
                        size=10000)
    return {i["_source"]["key"]:i["_source"]["value"] for i in results["hits"]["hits"]}

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

# _nuke_schema(es)
# _seed_schema(es)


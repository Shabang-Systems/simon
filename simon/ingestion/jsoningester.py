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

from ..components.documents import *
from ..models import *


### Ingest Remote Helpers ###
# These helpers should take a URL, and return an
# array of flat dictionaries with flat data fields.
# Like [ {"this": 1, "that": "two"}, {"what": 1, "the": "hell"} ]

class JSONIngester:
    def __init__(self, context:AgentContext):
        self.__context = context

    ## Ingest Remote Function ###
    def ingest(self, url, mappings:Mapping, delim="\n", local=False):
        """Read and index a remote resource into Elastic with a field mapping

        Note
        ----
        This function is useful for STRUCTURED DATA. For SINGLE FILES/PAGES,
        use `ingest_remote`


        Parameters
        ----------
        url : str
            URL to read.
        mappings : Mapping
            Which fields match with what index? 
        delim : optional, str
            How do we deliminate chunks? Perhaps smarter in the future but
            for now we are just splitting by a character.
        local : optional, bool
            Is this JSON a local file?

        Return
        ------
        List[str]
            List of hashes of the data we have read
        """

        context = self.__context
        L.info(f"Creating JSON indexing task on {url}...")

        # check mappings
        mappings.check()

        # download page
        if local:
            with open(url, 'r') as df:
                data = json.load(df)
        else:
            headers = {'user-agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers)

            data = r.json()

        L.debug(f"Succesfuly fetched {url}.")

        # create documents
        docs = [parse_text(**{map.dest.value:i[map.src] for map in mappings.mappings},
                           delim=delim)
                for i in data]
        # filter for those that are indexed
        docs = list(filter(lambda x:(get_fulltext(x.hash, context)==None), docs))

        L.debug(f"Going to index {len(docs)} documents for JSON indexing.")

        # pop each into the index
        # and pop each into the cache and index
        for i in docs:
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
        L.info(f"Done creating JSON index on {url}")

        # return hashes
        return [i.hash for i in docs]


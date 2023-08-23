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
    def ingest(self, url, mappings:Mapping, delim="\n", local=False, load=100):
        """Read and index a remote resource into the database with a field mapping

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
        load : optional, int
            The load to give to the ingester

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

        L.debug(f"Succesfuly fetched {url}. Parsing...")

        # create documents
        docs = [parse_text(**{map.dest.value:i[map.src] for map in mappings.mappings},
                           delim=delim)
                for i in data]
        # filter for those that are indexed
        docs = list(filter(lambda x:(get_fulltext(x.hash, context)==None), docs))

        L.debug(f"Going to index {len(docs)} documents for JSON indexing.")

        # pop each into the index
        # and pop each into the cache and index
        for i in range(0, len(docs), load):
            L.debug(f"Ingesting batch {i//load}/{len(docs)//load}")
            bulk_index(docs[i:i+load], context)
        # refresh
        L.info(f"Done creating JSON index on {url}")

        # return hashes
        return [i.hash for i in docs]


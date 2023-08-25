"""
ocringester.py
Uses Tika + Tesseract OCR to read a local or remote file
This could be images, PDFs, websites, or any amount of goodies.
"""

# System Library
import os
import re
import time
import hashlib
import mimetypes
from typing import List
from itertools import groupby, islice
import tempfile


import errno
import shutil
import tempfile


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

class OCRIngester:
    def __init__(self, context:AgentContext):
        self.__context = context

    def ingest_file(self, path, title=None, source=None):
        """OCR and Ingest a local file using Tika

        Parameters
        ----------
        path : str
            Path of the local file to read.
        title : optional, str
            The title of the document, passed to the LLM.
        source : optional, str
            The "source" of the LLM, arbiturary string not exposed to
            the LLM.

        Returns
        ------
        str
            Hash of the document we have read.
        """
        L.info(f"OCR Ingesting {path}...")
        doc = parse_tika(path, title=title, source=(source if source else path))
        L.debug(f"Tika parsed {path}.")
        index_document(doc, self.__context)
        L.debug(f"{path} sucessfully indexed.")

        # return hashes
        return doc.hash

    def __ingest_remote_document(self, request, uri, title=None, source=None):
        fp = None
        try:
            L.debug(f"Creating temporary path...")
            tmp_dir = tempfile.mkdtemp()  # create dir
            f = os.path.join(tmp_dir, f"simon-cache-{time.time()}")
            L.debug(f"Dumping content...")
            fp = open(f, 'wb')
            fp.write(request.content)
            return self.ingest_file(f, title, (source if source else uri))
        finally:
            try:
                if fp:
                    fp.close()
                shutil.rmtree(tmp_dir)  # delete directory
            except OSError as exc:
                if exc.errno != errno.ENOENT:  # ENOENT - no such file or directory
                    raise  # re-raise exception


    def ingest_remote(self, uri, title=None, source=None):
        """OCR and Ingest a remote file using Tika

        Parameters
        ----------
        uri : str
            The path to the online URI.
        title : optional, str
            The title of the document, passed to the LLM.
        source : optional, str
            The "source" of the LLM, arbiturary string not exposed to
            the LLM.

        Returns
        ------
        str
            Hash of the document we have read.
        """

        L.info(f"OCR Ingesting Remote {uri}...")
        # Search for the URL in the cache if it exists
        hash = get_hash(uri, self.__context)

        if hash:
            L.debug(f"Hash is found in the cache; we are done.")
            return hash

        L.debug(f"Attempting to fetch {uri}...")
        headers = {'user-agent': 'Mozilla/5.0'}
        r = requests.get(uri, headers=headers)
        content_type = r.headers['content-type'].split(";")[0].strip()

        if "text" in content_type:
            L.info(f"BeautifulSoup Ingesting Web Page {uri}...")
            doc = parse_web(r.content, title, source=uri)
            hash = doc.hash
            index_document(doc, self.__context)
            L.debug(f"{uri} successfully indexed.")
        elif "application" in content_type:
            hash = self.__ingest_remote_document(r, uri, title, source)
        elif "image" in content_type:
            hash = self.__ingest_remote_document(r, uri, title, source)

        # and pop it into the cache and index
        cache(uri, hash, self.__context)

        # return hashes
        return hash


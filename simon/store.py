"""
store.py
Ingested Data Management
"""

import logging
L = logging.getLogger("simon")

from .models import AgentContext
from .components.documents import *
from .ingestion.ocringester import OCRIngester

class Datastore:
    """DataStore management utility

    Parameters
    ----------
    context : AgentContext
        The context to start using the agent from.
    """

    def __init__(self, context:AgentContext):
        self.__context = context
        self.__ingester = OCRIngester(context)

    def store(self, uri:str, title:str=None, warn=True):
        """Ingest a single document from the internet (PDF, websites, etc.)

        Parameters
        ----------
        uri : str
            An internet address pointing to the document to index.
        title : optional, str
            The title of the document you are storing, which is
            exposed to the LLM.
        warn : optional, str
            Whether to point the dummy-usage warning.

        Returns
        -------
        str
            The hash of the newly indexed document.
        """
        
        if warn:
            L.warn(f"You are using the high-level DataStore API to ingest a single URI from the internet with OCR, which is pretty limiting set of options.")
            L.warn(f"Though this works to quickly index a URL, you are encouraged to check out the full suite of ingesters at `simon.ingesters`.")
            L.warn(f"To mute this warning, pass warn=False to this function.")

        return self.__ingester.ingest_remote(uri, title)

    def delete(self, hash:str):
        """Delete a document by its hash.

        Parameters
        ----------
        hash : str
            The hash of the document to delete, returned from lookups.
        """
        
        L.info(f"Deleting document by the hash of {hash}!")
        delete_document(hash, self.__context)

    def get(self, hash:str):
        """Get the full text from a hash.

        Parameters
        ----------
        hash : str
            The hash of the document to get the full text from.

        Returns
        -------
        Optional[str]
            The full text of the document.
        """
        
        return get_fulltext(hash, self.__context)

    def highlights(self, hash:str, k=3):
        """Returns the chunks with top TFIDF of a document.

        Parameters
        ----------
        hash : str
            The hash of the document to look up highlights to.
        k : optional, int
            The number of highlight chunks to return.

        Returns
        -------
        List[str]
            The highlighted important chunks.
        """
        
        return top_tf(hash, self.__context)


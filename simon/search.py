import logging
L = logging.getLogger("simon")

# import our tools
from .models import *
from .kb import *
from .components.documents import *

# RIO, Followup, and Reason
from .agents import *

# threading!
import threading
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

# threadnig helper
# https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread
_DEFAULT_POOL = ThreadPoolExecutor()

def threadpool(f, executor=None):
    @wraps(f)
    def wrap(*args, **kwargs):
        return (executor or _DEFAULT_POOL).submit(f, *args, **kwargs)

    return wrap

class Search:
    def __init__(self, context: AgentContext, verbose=False):
        #  knowledge base
        self.__kb = KnowledgeBase(context)

        # agents
        self.__rio = RIO(context, verbose)
        self.__reason = Reason(context, verbose)

        #### Context ####
        self.__context = context

    def query(self, text, streaming=False):
        """invokes the inference cycle

        uses all of the Assistant's tools to create an inference

        Parameters
        ----------
        text : str
            the string input query
        streaming : optional, bool
            Return a generator for streaming instead

        Returns
        -------
        Optional[dict]
            the output, with resource information, etc. if not streaming;
            otherwise its passed to streaming
        """

        assert type(text) == str, f"Unexpected non-string pased to Search.query: {text}"
        if text.strip() == "":
            raise ValueError(f"Empty query found to Search.query! Please supply a query that is non-empty. Current query: {text}")

        @threadpool
        def process():
            # fix the query and brainstorm possible
            # tangentia questions. use both to search the resource
            # we first query for relavent resources, then performing
            # search with them. if no results are return, don't worry
            # we just filter them out
            L.info(f"Serving query \"{text}\"...")
            resources = self.search(text) # to filter out errors and flatten
            L.debug(f"Search on \"{text}\" complete")

            if not resources:
                # if there's no valid resources found,
                # return nothing
                return None

            # L.debug("REASONING")
            output = self.__reason(text, resources, streaming)
            return output

        results_promise = process()
        if not streaming:
            res = results_promise.result()
            L.debug(f"Query complete for \"{text}\"")
            return res

        # if we are streaming, start doing that
        def stream_generator():
            results_generator = results_promise.result()
            for i in results_generator:
                yield i

        return stream_generator()

    def brainstorm(self, text, streaming=False):
        """Use the RIO to brainstorm followup questions

        Uses the RIO to come up with follow-up questions given a
        string of text, and then proceed to try to answer it using
        simon

        Parameters
        ----------
        text : str
            The text to come up with follow up questions
        fix : optional, bool
            Whether to call queryfixer
        streaming : optional, bool
            Return a generator for streaming instead

        Returns
        -------
        List[Dict[str, Union[List[str]|str]]]
            Each follow up question, and the response if exists.
            [{"goal": goal of the user,
                "questions": [follow up questions]
            }]
        """

        assert type(text) == str, f"Unexpected non-string pased to Search.brainstorm: {text}"
        if text.strip() == "":
            raise ValueError(f"Empty query found to Search.brainstorm! Please supply a query that is non-empty. Current query: {text}")

        @threadpool
        def process():
            L.info(f"Serving prefetch \"{text}\"...")
            # entities = self.__entity_memory.load_memory_variables({"input": text})["entities"]
            kb = self.search(text) # we only search the kb because this is only a spot check
            L.info(f"Search complete for \"{text}\".")

            observation = self.__rio(text, kb, streaming)
            return observation

        results_promise = process()

        if not streaming:
            res = results_promise.result()
            L.debug(f"Prefetch reasoning complete for \"{text}\"")
            return res

        # if we are streaming, start doing that
        def stream_generator():
            results_generator = results_promise.result()
            for i in results_generator:
                yield i

        return stream_generator()
        

    def search(self, text):
        assert type(text) == str, f"Unexpected non-string pased to Search.search: {text}"
        if text.strip() == "":
            raise ValueError(f"Empty query found to Search.search! Please supply a query that is non-empty. Current query: {text}")

        # query the kb first
        res = self.__kb(text)

        if type(res) == SimonProviderError:
            return

        # unserialize the provider responses
        serialized = [{"text": r.body,
                       "metadata": {
                           "source": r.metadata["source"],
                           "hash": r.metadata["hash"],
                           "title": r.title,
                       }} for r in res]


        return serialized

    def autocomplete(self, query:str):
        """Autocomplete the document with the given title

        Parameters
        ----------
        query : str
            The partial title of the document to start suggesting from.

        Returns
        -------
        List[Tuple[str, str]]
            A list of (title, text).
        """

        assert type(query) == str, f"Unexpected non-string pased to Search.autocomplete: {query}"
        
        return list(sorted(set(autocomplete(query, self.__context))))

    def levenshteinDistance(s1, s2):
        if len(s1) > len(s2):
            s1, s2 = s2, s1

        distances = range(len(s1) + 1)
        for i2, c2 in enumerate(s2):
            distances_ = [i2+1]
            for i1, c1 in enumerate(s1):
                if c1 == c2:
                    distances_.append(distances[i1])
                else:
                    distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
                    distances = distances_
        return distances[-1]

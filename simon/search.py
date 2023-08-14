import logging
L = logging.getLogger("simon")

# import our tools
from .models import *
from .kb import *
from .components.documents import *

# RIO, Followup, and Reason
from .agents import *

class Search:
    def __init__(self, context: AgentContext, verbose=False):
        #  knowledge base
        self.__kb = KnowledgeBase(context)

        # agents
        self.__rio = RIO(context, verbose)
        self.__fix = QueryFixer(context, verbose)
        self.__reason = Reason(context, verbose)

        #### Context ####
        self.__context = context

    def query(self, query, groupby="source"):
        """invokes the inference cycle

        uses all of the Assistant's tools to create an inference

        Parameters
        ----------
        query : str
            the string input query
        groupby : str
            the metadata field to group references by

        Returns
        -------
        dict
            the output, with resource information, etc.
        """

        L.info(f"Serving query \"{query}\"...")
        # fix the query and brainstorm possible
        # tangentia questions. use both to search the resource
        # we first query for relavent resources, then performing
        # search with them. if no results are return, don't worry
        # we just filter them out
        brainstorms =self.brainstorm(query) 
        questions = [query] + brainstorms
        L.debug(f"Prefetch on \"{query}\" complete")
        resources = [self.search(i) for i in questions]
        L.debug(f"Search on \"{query}\" complete")
        resources = [j for i in resources if i for j in i] # to filter out errors and flatten

        if resources == 0:
            # if there's no valid resources found,
            # return nothing
            return None

        # L.debug("REASONING")
        output = self.__reason(query, resources, brainstorms)
        L.debug(f"Reasoning on \"{query}\" complete")

        return output

    def brainstorm(self, text):
        """Use the RIO to brainstorm followup questions

        Uses the RIO to come up with follow-up questions given a
        string of text, and then proceed to try to answer it using
        simon

        Parameters
        ----------
        text : str
            The text to come up with follow up questions

        Returns
        -------
        List[Dict[str, Union[List[str]|str]]]
            Each follow up question, and the response if exists.
            [{"goal": goal of the user,
                "questions": [follow up questions]
            }]
        """

        L.info(f"Serving prefetch \"{text}\"...")
        # entities = self.__entity_memory.load_memory_variables({"input": text})["entities"]
        query = self.__fix(text)
        L.debug(f"Query semantic patching for \"{text}\" complete; patched query \"{query}\"")
        kb = self.__kb(query, True) # we only search the kb because this is only a spot check
        L.info(f"Search complete for \"{query}\".")

        observation = self.__rio(text, kb)
        L.debug(f"Prefetch reasoning complete for \"{text}\"")
        return observation

    def search(self, text):
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
        
        return suggest(query, self.__context)




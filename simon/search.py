import logging
L = logging.getLogger(__name__)

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
            the output, with widget information, etc.
        """

        # fix the query
        q = self.__fix(query)
        # first kb call always goes to internal knowledge
        # TODO is this a good idea?
        # L.debug("SEARCHING")
        kb = self.__kb(q)

        if not kb and kb == "":
            kb = "No documents was found in your knowledge base regarding this topic."

        # L.debug("REASONING")
        output = self.__reason(query, kb)

        # we now assemble the metadata all citations that come from the kb
        metadata = {}
        hashes = {}
        for id, text in output["references"].items():
            # if the id came from the kb (i.e. the index is smalller than kb
            if id < output["context_sentence_count"]["kb"]:
                result = search(text, self.__context, IndexClass.KEYWORDS, k=1)
                if len(result) == 1: # i.e. if match was sucessful
                                     # which sometimes it isn't
                    metadata[id] = result[0]["metadata"]
                    hashes[id] = result[0]["hash"]

        # we now parse and group reference info by source
        reference_sources = {}
        for key, value in metadata.items():
            group = value[groupby]

            if not reference_sources.get(group):
                reference_sources[group] = {}

            reference_sources[group][key] = {
                "text": output["references"][key],
                "metadata": value
            }

            reference_sources[group]["_hash"] = hashes[key]

        # for each one, we also sort based on their eq id

        # this key is not useful for any purpose except for matching
        del output["context_sentence_count"]
        del output["resources"]
        del output["references"]
        output["resource_references"] = reference_sources
        output["resource_ids"] = {i:j[groupby] for i, j in metadata.items()}

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

        # entities = self.__entity_memory.load_memory_variables({"input": text})["entities"]
        query = self.__fix(text)
        kb = self.__kb(text) # we only search the kb because this is only a spot check

        observation = self.__rio(text, kb)
        return observation

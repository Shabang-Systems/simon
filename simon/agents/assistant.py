from langchain.memory import ConversationEntityMemory, ConversationSummaryMemory, CombinedMemory
from langchain.prompts import BaseChatPromptTemplate, PromptTemplate
from langchain.chains import LLMChain
from langchain.agents import AgentOutputParser, LLMSingleActionAgent, AgentExecutor
from langchain.schema import AgentAction, AgentFinish, HumanMessage, OutputParserException, SystemMessage, AIMessage
from langchain.tools import BaseTool, Tool

import re
from typing import List, Union
from datetime import datetime

from ..models import *
from ..utils.elastic import kv_set, kv_getall

from ..components.documents import *
from .querymaster import *
from .queryfixer import *
from ..providers import *
from ..widgets import *
from .rio import *
from .followup import *
from .reason2 import *


import logging
L = logging.getLogger(__name__)

class Assistant:
    def __init__(self, context, providers=[], widgets=[], verbose=False):
        """Creates a simon assistant

        Parameters
        ----------
        context : AgentContext
            The context to create the assistant from.
        providers : List[SimonProvider]
            The tools Simon can use.
        widgets : List[SimonWidget]
            The widgets used to format the output text.
        verbose : optional, bool
            Whether or not to show intermediate steps. Defaults to False.
        """

        #### SEED DEFAULT PROVIDERS AND WIDGETS ####
        # the knowledgebase is a special provider which is queried every time
        self.__kb = KnowledgeBase(context)

        # other providers
        providers = providers
        widgets += get_widget_suite(context)

        self.__provider_options = {i.selector_option:i for i in providers}
        self.__provider_qm = QueryMaster(context, list(self.__provider_options.keys())+[
            QuerySelectorOption("No suitable options in this list is found.", "error")
        ], "answer the question", verbose)

        self.__widget_options = {i.selector_option:i for i in widgets}
        self.__widget_qm = QueryMaster(context, list(self.__widget_options.keys()), "present the information", verbose)

        #### Answer Selector QM ####
        self.__validator_options = [
            QuerySelectorOption("This answer is a sufficient, and well-reasoned answer to the question.", "success"),
            QuerySelectorOption("This answer is an indirect answer to the question.", "clarify"),
            QuerySelectorOption("The model was unable to answer the question due to a technical reason.", "error")
        ]

        self.__validator_qm = QueryMaster(context, self.__validator_options, "verify whether or not the given answer is a sufficient answer for the question.", verbose)

        #### MEMORY ####
        # create the entity memory
        # self.__entity_memory = ConversationEntityMemory(llm=context.llm, input_key="input")
        # kv = kv_getall(context.elastic, context.uid)
        # self.__entity_memory.entity_store.store = kv

        #### RIO, Followup, and Reason ####
        self.__rio = RIO(context, verbose)
        self.__followup = Followup(context, verbose)
        self.__reason = Reason(context, verbose)
        self.__fix = QueryFixer(context, verbose)

        #### Context ####
        self.__context = context

    def __call__(self, query, groupby="source"):
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

        import time

        # L.debug("START RECALL")
        # L.debug("LOADING")
        # and create the first reasoning group
        # entities = self.__entity_memory.load_memory_variables({"input": query})["entities"]

        # L.debug("FIXING")
        # fix the query
        q = self.__fix(query)
        # first kb call always goes to internal knowledge
        # TODO is this a good idea?
        # L.debug("SEARCHING")
        kb, providers = self.search(q, return_provider_results=True)

        # L.debug("REASONING")
        output = self.__reason(query, kb, providers)


        # we now assemle the metadata all citations that come from the kb
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

        # save results into memory
        # L.debug("SAVING")
        # input_dict = {"input": query}
        # self.__entity_memory.save_context(
        #     input_dict,
        #     {"output": output["answer"]}
        # )

        # L.debug("DONE")
        # 
        # and now, store memory results
        # kv = self.knowledge

        # # store memory context key value in elastic
        # for key,value in kv.items():
        #     kv_set(key, value, self.__context.elastic, self.__context.uid)

        #     "load": onfix-onload,
        #     "fix": onsearch-onfix,
        #     "search": onreason-onsearch,
        #     "reason": onsave-onreason,
        #     "save": onpost-onsave,
        #     "post": ondone-onpost,
        # })
        # and render it as the correct widget
        # L.debug("WIDGETING")
        # widget_option = self.__widget_qm(answer)
        # widget = self.__widget_options[widget_option]

        return output


    #### KNOWLEDGE ####
    # kb setters
    def store(self, title, content, source=""):
        """Force the model to explicitly remember something

        Parameters
        ----------
        title : str
            The title of the infromation to store.
        content : str
            The content of the information.
        source : str
            The source of the information.
        """

        document = parse_text(content, title, source)
        hash = index_document(document, self.__context)

        return document.hash

    def read(self, url) -> str:
        """ask the assistant to read a URL

        Parameters
        ----------
        url : str
            the string URL to read

        Returns
        -------
        str
            the hash of the read document
        """

        hash = read_remote(url, self.__context)

        return hash

    # kb getters
    def search(self, query, return_provider_results=False):
        """search the knowledgebase for some piece of information

        Parameters
        ----------
        query : str
            the string query to search the kb with
        return_provider_results : optional, bool
            whether to return results that came from third-party providers.
            default false as we default to simple search

        Returns
        -------
        str
            the knowledgebase's answer
        """

        # query the kb first
        res = self.__kb(query)

        if res == "We found nothing. Please rephrase your question.":
            res = ""
        

        provider_res = ""


        if return_provider_results and len(self.__provider_options) != 0:
            # ask qm to choose what additinoal provider to use
            option = self.__provider_qm(query)

            # if an additional provider is chosen, we provide from it
            if option.id != "error":
                provider = self.__provider_options[option]
                provider_res = "\n---\n"+provider(query.strip('"').strip("'").strip("\n").strip())
        else:
            provider_res = ""

        # if provider result is just the prefix, its nothing
        if provider_res.strip() == "---":
            provider_res = ""
            
        # if we indeed have nothing
        if (res+provider_res).strip() == "":
            res = "We found nothing. Please rephrase your question."

        # return the actual data
        # with warning
        return (res, provider_res) if return_provider_results else (res)

    def autocomplete(self, query):
        """Autocomplete a document title

        Parameters
        ----------
        q : query
            The query to autocomplete
        """

        return suggest(query, self.__context)


    def fetch(self, hash) -> str:
        """get the fulltext of an URL

        Parameters
        ----------
        hash : str
            the hash of the read document

        Returns
        -------
        str
            the full text of a particular document
        """

        return get_fulltext(hash, self.__context)

    def summarize(self, hash) -> str:
        """make the agent summarize a text

        Parameters
        ----------
        hash : str
            the hash of the read document

        Returns
        -------
        usual simon output
        """

        context = "\n".join(top_tf(hash, self.__context))
        template = PromptTemplate.from_template("System: You are an AI that is going to summarize the text given. Human: Here is the text {input}. Begin! AI:")
        chain = LLMChain(llm=self.__context.llm, prompt=template)

        return chain.run(input=context)

    # kb deleters
    def forget(self, hash):
        """ask the assistant to forget a document/stored element

        Notes
        -----
        This is distinct from self._forget_memory because
        this UNDOs the self.read() or self.store() operation by removing
        the hash token of the document the assistant has read.

        Parameters
        ----------
        hash : str
            the hash to forget
        """

        delete_document(hash, self.__context)

    # #### MEMORY ####
    # def _forget_memory(self, key):
    #     """Forgets a piece of memory

    #     Parameters
    #     ----------
    #     key : str
    #         The key-palue fact to delete.
    #     """

    #     kv = kv_getall(self.__context.elastic, self.__context.uid)
    #     del kv[key]
    #     self.__entity_memory.entity_store.store = kv
    #     kv_delete(key, self.__context.elastic, self.__context.uid) 


    #### RIO ####
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

        # observe answe
        import time

        # entities = self.__entity_memory.load_memory_variables({"input": text})["entities"]
        query = self.__fix(text)
        kb = self.__kb(text) # we only search the kb because this is only a spot check

        observation = self.__rio(text, kb)
        return observation


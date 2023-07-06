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
from ..providers import *
from ..widgets import *
from .rio import *
from .followup import *
from .reason import *

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
        self.__entity_memory = ConversationEntityMemory(llm=context.llm, input_key="input")
        kv = kv_getall(context.elastic, context.uid)
        self.__entity_memory.entity_store.store = kv

        #### RIO, Followup, and Reason ####
        self.__rio = RIO(context, verbose)
        self.__followup = Followup(context, verbose)
        self.__reason = Reason(context, verbose)

        #### Context ####
        self.__context = context

    def __call__(self, query):
        """invokes the inference cycle

        uses all of the Assistant's tools to create an inference

        Parameters
        ----------
        query : str
            the string input query

        Returns
        -------
        dict
            the output, with widget information, etc.
        """

        # first kb call always goes to internal knowledge
        # TODO is this a good idea?
        kb = self.search(query)

        # and create the first reasoning group
        entities = self.__entity_memory.load_memory_variables({"input": query})["entities"]
        answer = self.__reason(query, kb)
        self.__entity_memory.save_context(
            {"input": query},
            {"output": answer}
        )
        judgement = self.__validator_qm(f"Question: {query}. Answer: {answer}")

        # a force breaking mechanism
        recall_count = 0

        # state_id is the validator's judgement of the quality of the answer
        # we re-prompt until it is happy with the answer or gives up
        while judgement.id == "clarify" and recall_count < 4:
            recall_count += 1 
            # calculate clarification
            clarification = self.__followup(query, answer, entities)
            followup = clarification.followup

            # followup entities
            input_dict = {"input": (query+"\n"+followup)}
            entities = self.__entity_memory.load_memory_variables(input_dict)["entities"]
            kb += self.search(followup)

            # and re-reason
            answer = self.__reason(query, kb, entities)
            self.__entity_memory.save_context(
                input_dict,
                {"output": answer}
            )
            judgement = self.__validator_qm(f"Question: {query}. Answer: {answer}")

        # and now, store memory results
        kv = self.knowledge

        # store memory context key value in elastic
        for key,value in kv.items():
            kv_set(key, value, self.__context.elastic, self.__context.uid)

        # and render it as the correct widget
        widget_option = self.__widget_qm(answer)
        widget = self.__widget_options[widget_option]

        return {
            "raw": answer,
            "widget": widget_option.id,
            "payload": widget(answer)
        }


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
    def search(self, query):
        """search the knowledgebase for some piece of information

        Parameters
        ----------
        query : str
            the string query to search the kb with

        Returns
        -------
        str
            the knowledgebase's answer
        """

        # query the kb first
        res = self.__kb(query)
        
        # ask qm to choose what additinoal provider to use
        option = self.__provider_qm(query)

        # if an additional provider is chosen, we provide from it
        if option.id != "error":
            provider = self.__provider_options[option]
            res += "\n---\n"+provider(query.strip('"').strip("'").strip("\n").strip())

        # return the actual data
        # with warning
        return res

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

    #### MEMORY ####
    def _forget_memory(self, key):
        """Forgets a piece of memory

        Parameters
        ----------
        key : str
            The key-value fact to delete.
        """

        kv = kv_getall(self.__context.elastic, self.__context.uid)
        del kv[key]
        self.__entity_memory.entity_store.store = kv
        kv_delete(key, self.__context.elastic, self.__context.uid) 


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

        # observe answer
        entities = self.__entity_memory.load_memory_variables({"input": text})["entities"]
        observation = self.__rio(text, entities)
        return {"goal": observation.goal,
                "questions": observation.followup}


    @property
    def knowledge(self):
        return self.__entity_memory.entity_store.store



        

"""
reason.py
The natural language reasoning engine.
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import BaseOutputParser
from langchain.callbacks.base import BaseCallbackHandler

import logging
L = logging.getLogger("simon")


import threading

from collections import defaultdict

from nltk import sent_tokenize
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from ..models import *

import re

# You will be provided sources to come up with an answer. When creating your answer, adhere to the following four-element format:

# Help the user come up information they wouldn't have possibly thought of regarding the Concept and fill in any gaps in knowledge they have betrayed through their question by extrapolating in a markdown list like so:
# Provide a *full* full answer to the user's question. [4] Provide references to useful citation numbers in brackets found in the knowledge section *throughout* your answer after each claim; don't put a bunch all in the end. [2] You must only use information presented in the Knowledge section to provide your answer. [5] Use **markdown** _styles_, if appropriate. 

# . This list should only contain things that you mentioned above as should be included, and NOT contain anything that you mention was irrelevant. These results, together, should directly answer the user's question, in addition to fill in any gaps of knowledge the user has betrayed through their question. Include a five word or so headline, and a SINGLE link to the resource you want to present as a search result:

SYSTEM_TEMPLATE = """
You are helping a human understand the state of a concept by being a search engine. You will be provided textual knowledge which you must refer to during your answer. At the *end* of each sentence in knowledge you are given, there is a citation take in brakets [like so] which you will refer to. The user will provide you with a Query:, which will either be a question or a phrase used to initialize a search. Order the results of your search by RELAVENCE; keep the most direct answer to the user's query on top.

When responding, you must provide three sections: the sections are "Thought", "Search Results", "Answer". 

Thought: important elements in the knowledge base that SHOULD be included in the results, and important keywords that SHOULDN'T but was in the knowledge base anyways; keep this response under 5 words
Search Results: identify the results of your search. Include only things you mentioned above as relavent, and not those that you mentioned was not. The user should have a complete understanding of their question after reading these results. To present the results, follow this pattern
- five word headline for the result here, then a *single* citation tag next [1]
- repeat. five word headline, then a single citation tag [5]
- ...
- ...
- ...
- ...
[This can repeat *at most* N times, but the user hates reading so keep it short.]
Answer: If no resources are relavent and you can't answer the question, write the letters N/A here. Otherwise, provide an EXTREMELY BRIEF (< 2 sentences), FULL answer [3] to the users' query, include tages [3] to the search results you have above [5] SYNTHESIZE: don't just list out the resources again; describe and summarize the overall theme of the resources. [3]

When coming up with your headline, ensure the headlines all provide an answer to the user's question. You should not have colons (:) or quotes (") in the headline.

When coming up with your Search Results, *RANK THEM* based on the order of relavence. The most relavent result should be on top.

When coming up with your answer, don't just bundle tags [3] in the end of your answer. Spread them after each of your points [4].

You maybe provided resources that are entirely irrelavent. If so, *don't include them!* Use your best judgement to select resources and answers that will help you answer the question. Fact chec the resources; if something doesn't make sense, don't include it. Instead, provide Answer: N/A.

Begin!
"""

HUMAN_TEMPLATE = """
Knowledge: 
{kb}

Query:
{input}
"""

AI_TEMPLATE="""
Thought:
"""

class ReasonPromptFormatter(BaseChatPromptTemplate):
    def format_messages(self, **kwargs):
        return [SystemMessage(content=SYSTEM_TEMPLATE),
                HumanMessage(content=HUMAN_TEMPLATE.format(kb=kwargs["kb"],
                                                           input=kwargs["input"])),
                AIMessage(content=AI_TEMPLATE)]

class ReasonOutputParser(BaseOutputParser):
    def parse(self, str):
        str = str.strip("```output").strip("`").strip()

        regex = r"\n\n?Answer\s*:\s*(.*)"
        answer_match = re.search(regex, str, re.DOTALL)

        str = re.sub(regex, "", str).strip()

        regex = r"\s*(.*)\n\n?Search Results\s*:\s*(.*)"
        match = re.search(regex, str, re.DOTALL)

        if match:
            thought = match.group(1).strip("\"").strip('"').strip("`").replace("`", "").strip()
            extrapolations = match.group(2).strip("\"").replace('"', '').strip("`").replace("`", "").strip()
            if answer_match and answer_match.group(1):
                answer = answer_match.group(1).strip("\"").strip('"').strip("`").replace("`", "").strip()
            else:
                answer = ""
        else:
            answer = str.strip("\"").strip('"').strip("`").strip()
            extrapolations = ""

        # collect up all the [citations]
        resource_regex = r"\[(\d+)\]"
        resource_ids = []
        for r in re.findall(resource_regex, answer):
            resource_ids.append(int(r.strip()))

        extrapolations = [i.strip()[2:].strip("\"").strip('"').strip() for i in extrapolations.split("\n")]

        # collect up the extrapolation citations
        ex_citations = []
        for extrapolation in extrapolations:
            # get the extrapolation id
            results = list(re.findall(resource_regex, extrapolation))
            if len(results) == 0:
                ex_citations.append(-1)
                continue

            for r in results:
                ex_citations.append(int(r.strip()))
                continue
        # and we now remove all the citatinos from the extrapolations
        extrapolations = [re.sub(resource_regex, "", i).strip() for i in extrapolations]

        return {
            "answer": answer if answer != "" else None,
            "answer_resources": resource_ids,
            "search_results": [{"headline": i,
                                "resource": j} for i,j in zip(extrapolations, ex_citations)],
        }


# TODO the streaming API is currently really poorly designed
# so TODO make it better lol - hjl
class ReasonSingleUseCallbackHandler(BaseCallbackHandler):
    def __init__(self, formatter, destructor):
        self.__scratchpad = ""
        self.__formatter = formatter
        self.__destructor = destructor
        self.__cache = None
        self.__last_output = None
        self.done = False

    def blocking_next(self):
        while not self.__last_output:
            if self.done:
                break

        lo = self.__last_output
        self.__last_output = None
        return lo

    def on_llm_new_token(self, **kwargs):
        self.__scratchpad += kwargs["token"]

        out = self.__formatter(self.__scratchpad)
        if out and out != self.__cache:
            self.__cache = out
            self.__last_output = {"output": self.__cache, "done": False}

    def on_llm_end(self, res, **kwargs):
        self.__last_output = {"output": self.__cache, "done": True}
        self.done = True
        self.__destructor()

class Reason(object):
    def __init__(self, context, verbose=False):
        """Natural Language Reasoning engine

        Parameters
        ----------
        context : AgentContext
            The context to operate the RIO under
        verbose : bool
            Whether the chain should be verbose
        """
        
        self.__prompt = ReasonPromptFormatter(input_variables=["input", "kb"],
                                              output_parser=ReasonOutputParser())
        self.__chain = LLMChain(llm=context.reason_llm, prompt=self.__prompt, verbose=verbose)


    def __postprocess_res(self, res, kb, resource_ids, chunks):
        # if we have no response, return
        if res["answer"] and res["answer"].lower().strip() == "n/a":
            return 

        # set answer citations and the result citations
        res["answer_resources"] = {i: {"quote": resource_ids[i],
                                       "chunk": kb[chunks[i]]} for i in res["answer_resources"]}
        try:
            for i in res["search_results"]:
                id = i["resource"]

                i["resource"] = {"quote": resource_ids[id],
                                 "chunk": kb[chunks[id]]}
        except KeyError:
            return

        return res

    def __call__(self, input, kb, streaming=None):
        # initialize the dictionary for text-to-number labeling
        # this dictionary increments a number for every new key
        resource_ids = defaultdict(lambda : len(resource_ids))

        # chunk the resource into sentences and label them
        # this is a dictionary of resource_id:kb_entry
        chunks = {k:v
                  for indx, i in enumerate(kb)
                  for k,v in [(resource_ids[j], indx)
                              for j in sent_tokenize(i["metadata"]["title"]+" "+i["text"])]}

        # freeze and reverse the resource id dictionary
        # so this is now a dict of resource_id:text
        resource_ids = {v:k for k, v in resource_ids.items()}

        # tack the numerical labels onto the actual chunks into a big
        # context string
        # hard limit of 5500
        sentences = "".join([text+f" [{indx}]\n " for indx, text in resource_ids.items()])[:5500]

        L.debug(f"Starting reasoning request!!!")

        # run llm prediciton

        # if we are streaming, inject the streaming tools into the llm
        # and parse accordingly
        if streaming:
            def format_callback(output):
                res = self.__prompt.output_parser.parse(output)
                return self.__postprocess_res(res, kb, resource_ids, chunks)

            def remove_callback():
                self.__chain.llm.callbacks = [i for i in self.__chain.llm.callbacks if type(i) != ReasonSingleUseCallbackHandler]
                
            # create the callback handler 
            callback = ReasonSingleUseCallbackHandler(format_callback, remove_callback)

            def streaming_generator():
                while not callback.done:
                    yield callback.blocking_next()

            # and bind it to the llm
            self.__chain.llm.streaming = True
            if type(self.__chain.llm.callbacks) == list:
                self.__chain.llm.callbacks.append(callback)
            else:
                self.__chain.llm.callbacks = [callback]

            self.__chain.llm.temperature = 0

            # kick that puppy into motion 
            thread = threading.Thread(target=self.__chain.predict,
                                      kwargs={"input": input,
                                              "kb": sentences.strip()})
            thread.start()
            # return nothing
            return streaming_generator()

        
        output = self.__chain.predict(input=input,
                                      kb=sentences.strip())
        res = self.__prompt.output_parser.parse(output)

        L.debug(f"All done now with reasoning")
        # perform postprocessing and return
        return self.__postprocess_res(res, kb, resource_ids, chunks)


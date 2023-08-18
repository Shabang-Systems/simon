"""
reason.py
The natural language reasoning engine.
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import BaseOutputParser

import logging
L = logging.getLogger("simon")


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

SYSTEM_TEMPLATE = """
You are helping a human understand the state of a concept by being a search engine. You will be provided textual knowledge which you must refer to during your answer. At the *end* of each sentence in knowledge you are given, there is a citation take in brakets [like so] which you will refer to. The user will provide you with a Query:, which will either be a question or a phrase used to initialize a search.

When responding, you must provide three sections: the sections are "Headline", "Search Results", "Answer". 

Thought: ONE SENTENCE (< 10 words) summarizing which elements of the knowledge base answers user's question, and which is likely irrelavent or opposite.
Search Results: identify the results of your search. This list should only contain things that you mentioned above as being relavent, and NOT contain anything that you mention was irrelevant. These results, together, should directly answer the user's question, in addition to fill in any gaps of knowledge the user has betrayed through their question:
- headline for the resource (in your headline, be sure to have an answer to if this is what the user is searching for?) (<10 words); don't just paraphrase the resource [1]
- repeat this; answer again is this what the user is searching for again in a headline (<10 words) and a *single* bracket link; do NOT paraphrase the resource [5]
- ...
- ...
- ...
- ...
[This can repeat *at most* 5 times, but the user hates reading so keep it short.]
Answer: an EXTREMELY BRIEF (< 2 sentences), FULL answer to the users' query, include tages [3] to the search results you have above [2] SYNTHESIZE: don't just list out the resources again; describe and summarize the overall theme of the resources.

For instance, here's an example format:

Thought: what is relavent, what is not (< 10 words)
Search Results:
- Brief citation headline answering why this is an answer; don't paraphrase the resource [4]
- Another citation headline; don't paraphrase [6]
Answer: your answer [3] goes here [2]; summarizing what you see across the resources

Four important tips:
1. If a result is not relavent (or opposite to) the user's request, DON'T INCLUDE IT
2. The knowledge you are provided *is not ordered* and can contain irrelavent content
3. Very selectively pick what would be useful to answer the users' question
4. Keep everything concise and precise; make it EASY TO READ.
5. MOST IMPORTANTLY: *order the results of your search by RELAVENCE; keep the most direct answer to the user's query on top*

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
        regex = r"\s*(.*)\n\n?Search Results\s*:\s*(.*)\n\n?Answer\s*:\s*(.*)"
        match = re.search(regex, str, re.DOTALL)

        if match:
            thought = match.group(1).strip("\"").strip('"').strip("`").replace("`", "").strip()
            extrapolations = match.group(2).strip("\"").strip('"').strip("`").replace("`", "").strip()
            answer = match.group(3).strip("\"").strip('"').strip("`").replace("`", "").strip()
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
            "answer": answer,
            "answer_resources": resource_ids,
            "search_results": [{"headline": i,
                                "resource": j} for i,j in zip(extrapolations, ex_citations)],
        }

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
        
        prompt = ReasonPromptFormatter(input_variables=["input", "kb"],
                                       output_parser=ReasonOutputParser())
        self.__chain = LLMChain(llm=context.reason_llm, prompt=prompt, verbose=verbose)

    def __call__(self, input, kb):
        # initialize the dictionary for text-to-number labeling
        # this dictionary increments a number for every new key
        resource_ids = defaultdict(lambda : len(resource_ids))

        # chunk the resource into sentences and label them
        # this is a dictionary of resource_id:kb_entry
        chunks = {k:v
                  for indx, i in enumerate(kb)
                  for k,v in [(resource_ids[j], indx)
                              for j in sent_tokenize(i["text"])]}

        # freeze and reverse the resource id dictionary
        # so this is now a dict of resource_id:text
        resource_ids = {v:k for k, v in resource_ids.items()}

        # tack the numerical labels onto the actual chunks into a big
        # context string
        # hard limit of 5500
        sentences = "".join([text+f" [{indx}]\n " for indx, text in resource_ids.items()])[:5500]

        L.debug(f"Starting reasoning request with context: -----\n{sentences}\n----- !!!")

        # run llm prediciton
        res =  self.__chain.predict_and_parse(input=input,
                                              kb=sentences.strip())

        # if we have no response, return
        if res["answer"].lower().strip() == "n/a":
            return 

        # set answer citations and the result citations
        res["answer_resources"] = {i: {"quote": resource_ids[i],
                                       "chunk": kb[chunks[i]]} for i in res["answer_resources"]}
        for i in res["search_results"]:
            id = i["resource"]

            i["resource"] = {"quote": resource_ids[id],
                             "chunk": kb[chunks[id]]}

        return res


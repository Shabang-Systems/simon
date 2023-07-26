"""
reason.py
The natural language reasoning engine.
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import BaseOutputParser

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
You are helping a human understand the state of a concept by being a search engine. You will be provided textual knowledge which you must refer to during your answer. At the *end* of each sentence in knowledge you are given, there is a citation take in brakets [like so] which you will refer to.

When responding, you must provide two sections: the sections are "Answer", "Search Results". 

Answer: Provide a full, *brief (<4 sentences)*, and fact-supported answer the user's question. [2] After each of your claims, provide a tag to the sentence you used to support your claim, like so: [3]. Use **markdown** _styles_, lists, etc. if appropriate. If the Knowledge section does not provide enough information to be able to answer the question with some reasoning from you, place the letters N/A here. 
Search Results: identify the sources from your search; if no results are found, place the letters N/A in this section. These should be resources from your knowledge section that directly answer the user's question, in addition to fill in any gaps of knowledge the user has betrayed through their question; respond in a markdown list:
- *extremely* brief headline here, don't use two parts like a colon; keep it short (<10 words) [1]
- repeat this process, provide an *very very short* headline (<10 words) and a bracket link [5]
- short headline (<10 words) and a link [8]
- ...
- ...
- ...
- ...
[This can repeat N times, but the user hates reading so keep it short. Like a search engine, put the most salient and relavent point on top, and order by relavence]

For instance, here's an example format:

Answer: your answer here [3], some elaborations too [8]. More here.
Search Results:
- Brief citation headline [4]
- Another citation headline [6]

The user is smart, but is in a rush. Keep everything concise and precise.

Begin!
"""

HUMAN_TEMPLATE = """
Knowledge: 
{kb}

Question:
{input}
"""

AI_TEMPLATE="""
Answer:"""

class ReasonPromptFormatter(BaseChatPromptTemplate):
    def format_messages(self, **kwargs):
        return [SystemMessage(content=SYSTEM_TEMPLATE),
                HumanMessage(content=HUMAN_TEMPLATE.format(kb=kwargs["kb"],
                                                           input=kwargs["input"])),
                AIMessage(content=AI_TEMPLATE)]


class ReasonOutputParser(BaseOutputParser):
    def parse(self, str):
        str = str.strip("```output").strip("`").strip()
        regex = r"\s*(.*)\n\n?Search Results\s*:\s*(.*)"
        match = re.search(regex, str, re.DOTALL)

        if match:
            answer = match.group(1).strip("\"").strip('"').strip("`").replace("`", "").strip()
            extrapolations = match.group(2).strip("\"").strip('"').strip("`").replace("`", "").strip()
        else:
            answer = str.strip("\"").strip('"').strip("`").strip()
            extrapolations = ""

        # collect up all the [citations]
        resource_regex = r"\[(\d+)\]"
        resource_ids = []
        for r in re.findall(resource_regex, str):
            resource_ids.append(int(r.strip()))

        extrapolations = [i.strip()[2:].strip("\"").strip('"').strip() for i in extrapolations.split("\n")]

        return {
            "answer": answer,
            "extrapolations": extrapolations,
            "resources": resource_ids
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

    def __call__(self, input, kb="", provider="", entities={}):
        provider_sentences = [j for i in provider.split("\n--\n") for j in sent_tokenize(i)]
        provider_sentences = [j for i in provider_sentences for j in i.split("\n")]

        num_provider_sents = len(provider_sentences)

        kb_sentences = [j for i in kb.split("\n--\n") for j in sent_tokenize(i)]
        kb_sentences = [j for i in kb_sentences for j in i.split("\n")]

        sentences = kb_sentences + provider_sentences

        sentence_dict = {indx:i.strip() for indx, i in enumerate(sentences)}
        sentences = "".join([i+f" [{indx}] " for indx, i in enumerate(sentences)])

        res =  self.__chain.predict_and_parse(input=input,
                                              kb=sentences)
        # we only leave useful resources
        res["resources"] = {int(i):sentence_dict.get(i, "") for i in res["resources"]}
        res["context_sentence_count"] = {
            "provider": len(provider_sentences),
            "kb": len(kb_sentences)
        }

        return res


"""
reason.py
The natural language reasoning engine.
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import StringPromptTemplate
from langchain.schema import BaseOutputParser

from ..models import *

import re

# You will be provided sources to come up with an answer. When creating your answer, adhere to the following four-element format:

TEMPLATE = """
System:
Use knowledge to answer the user's question.

Answer in the following four element format:

Knowledge:
Contents of your knowledge base should go here; recall any relavent (or perhaps adjacent and somewhat relevant) information to aid you.

Answer:
a markdown-formatted answer the human's question; use markdown lists, bold elements, italics, and quote your sources. rely *only* on information from the knowledge: section above.

Reasoning:
a reasoning about whether or not your answer is well supported by the sources

Better Question:
N/A, if your answer is sufficient; otherwise, provide a better question that would answer the Human's question but is more specific

Begin!

Human:
My question is: {input}

AI:

Knowledge:
{kb}

Answer:
"""

class ReasonPromptFormatter(StringPromptTemplate):
    def format(self, **kwargs):
        return TEMPLATE.format(kb=kwargs["kb"],
                                input=kwargs["input"])

class ReasonOutputParser(BaseOutputParser):
    def parse(self, str):
        str = str.strip("```output").strip("`").strip()
        regex = r"\s*(.*)\n\n?Reasoning\s*:\s*(.*)\n\n?Better Question\s*:\s*(.*)"
        match = re.search(regex, str, re.DOTALL)

        if match:
            answer = match.group(1).strip("\"").strip('"').strip("`").strip()
            reasoning = match.group(2).strip("\"").strip('"').strip("`").strip()
            followup = match.group(3).strip("\"").strip('"').strip("`").strip()
        else:
            return str, None

        if "n/a" in followup.lower():
            followup = None

        return answer, followup

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
        self.__chain = LLMChain(llm=context.llm, prompt=prompt, verbose=verbose)

    def __call__(self, input, kb="", entities={}):
        return self.__chain.predict_and_parse(input=input,
                                              kb=kb)

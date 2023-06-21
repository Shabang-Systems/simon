"""
querymaster.py
A few-shot classifier for knowledge queries with an llm
"""

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import StringPromptTemplate
from langchain.schema import BaseOutputParser

from typing import List
from dataclasses import dataclass

from .models import *

TEMPLATE = """
Available options:
{options}

To answer the question {input}, it is best to use Option """

class QuerySelectorTemplate(StringPromptTemplate):
    options: List[QuerySelectorOption]

    def format(self, **kwargs):
        options = "\n".join([f"Option {i}: {option.info}" for i, option in enumerate(self.options)])
        return TEMPLATE.replace("{options}", options).replace("{input}", kwargs["input"])

class SingleLetterOptionParser(BaseOutputParser):
    options: List[QuerySelectorOption]

    def parse(self, str):
        return self.options[int(str[0])]

#################

class QueryMaster:

    def __init__(self, context, qso, verbose=False):
        """Creates a simon query handler

        Parameters
        ----------
        context : AgentContext
            The context to create the assistant from.
        options : List[QuerySelectorOption]
            The options for the datasources.
        verbose : optional, bool
            Whether or not the chain should be verbose.
        """

        prompt = QuerySelectorTemplate(
            options=qso,
            input_variables=["input"],
            output_parser=SingleLetterOptionParser(options=qso)
        )

        self.__chain = LLMChain(llm=context.llm, prompt=prompt, verbose=verbose)

    def __call__(self, input):
        return self.__chain.predict_and_parse(input=input)


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

from ..models import *

TEMPLATE = """
You are an AI responsible for selecting the most optimal option based on
a query.

Available options:
{options}

When selecting options, ahdere to the following format.

Thought: why you are going to select the option you are going to select
Selection: *one number* representing the option you are selecting

You are now going to select an option to {action} {input}.

Remember to provide both a Thought: line *and* a Selection: line

Begin!

Thought:"""

class QuerySelectorTemplate(StringPromptTemplate):
    options: List[QuerySelectorOption]
    action: str = "answer the question"

    def format(self, **kwargs):
        options = "\n".join([f"Option {i}: {option.info}" for i, option in enumerate(self.options)])
        return TEMPLATE.format(options=options, input=kwargs["input"], action=self.action)

class SingleLetterOptionParser(BaseOutputParser):
    options: List[QuerySelectorOption]

    def parse(self, str):
        try:
            option = str.split("Selection:")[-1].strip()[0]
            return self.options[int(option)]
        except ValueError:
            breakpoint()

#################

class QueryMaster:

    def __init__(self, context, qso, action="answer the question", verbose=False):
        """Creates a simon query handler

        Parameters
        ----------
        context : AgentContext
            The context to create the assistant from.
        qso : List[QuerySelectorOption]
            The options for the datasources.
        action: optional, str
            The action that the query is selecting for
        verbose : optional, bool
            Whether or not the chain should be verbose.
        """

        prompt = QuerySelectorTemplate(
            options=qso,
            input_variables=["input"],
            output_parser=SingleLetterOptionParser(options=qso),
            action=action
        )

        self.__chain = LLMChain(llm=context.llm, prompt=prompt, verbose=verbose)

    def __call__(self, input):
        return self.__chain.predict_and_parse(input=input)


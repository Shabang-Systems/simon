"""
rio.py
I feel the need... The need for speed.

Helps a human do their tasks.
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import StringPromptTemplate
from langchain.schema import BaseOutputParser

from .models import *


TEMPLATE = """
System:
You are trying to creatively think of things that you haven't thought of before. You are given what you have already thought of, and you are responsible for brainstorming with follow up questions that provoke areas of extensions for your thoughts using questions that have a factual answer.

When replying with your questions, adhere to the following format.

Goal: what you are trying to achieve---beginning with the words "I am trying to..."
Questions:
[a markdown list, deliminated by -, of 3 most salient clarification, fact-based questions]

Remember, you maybe passed a *PARTIAL* slice of your thoughts. Hence, try to guess what the human is trying to say if their text is cut off awkwardly. 

Begin!

Thoughts:
{input}

Goal:"""

class RIOPromptFormatter(StringPromptTemplate):
    def format(self, **kwargs):
        return TEMPLATE.format(input=kwargs["input"])

class RIOOutputParser(BaseOutputParser):
    def parse(self, str) -> RIOObservation:
        goal, questions = str.split("Questions:")
        questions = [i.strip("-").strip()
                     for i in questions.strip().replace("\n -", "\n-").split("\n-")
                     if i.strip() != '']

        return RIOObservation(goal.strip(), questions)

class RIO(object):
    def __init__(self, context, verbose=False):
        """Context-Aware follow-up assistant

        Parameters
        ----------
        context : AgentContext
            The context to operate the RIO under
        verbose : bool
            Whether the chain should be verbose
        """
        
        prompt = RIOPromptFormatter(input_variables=["input"], output_parser=RIOOutputParser())
        self.__chain = LLMChain(llm=context.llm, prompt=prompt, verbose=verbose)

    def __call__(self, input):
        return self.__chain.predict_and_parse(input=input)

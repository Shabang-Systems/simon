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

from ..models import *


TEMPLATE = """
System:
You are creating margin notes to help creatively brainstorm an idea. You are going to be given your previous partial thoughts, and you are going to write comments (questions or statements) about these thoughts. Answering the comments you provide should help advance the partial thought you began with.

When replying with your comments, adhere to the following format.

Goal: what you are trying to achieve---beginning with the words "I am trying to..."
Comments:
- your first fact-based comment
- your second fact-based comment
[this could repeat at most 4 times, but should be usually kept to 2-3. They can be statements or questions. They should stand independently and not build off of each other.]

Remember, you maybe passed a *PARTIAL* slice of your thoughts. Hence, try to guess what the human is trying to say if their text is cut off awkwardly. 

Here are some supporting information:
{entities}

Begin!
{input}

Thoughts:
Goal:"""

class RIOPromptFormatter(StringPromptTemplate):
    def format(self, **kwargs):
        entities = "\n".join([
            f"{key}: {value}"
            for key,value in kwargs.pop("entities").items()])
        return TEMPLATE.format(input=kwargs["input"], entities=entities)

class RIOOutputParser(BaseOutputParser):
    def parse(self, str) -> RIOObservation:
        goal, questions = str.split("Comments:")
        questions = [i.strip("-").strip()
                     for i in questions.strip().replace("\n -", "\n-").split("\n-")
                     if i.strip() != '']

        return RIOObservation(goal.strip(), questions)

class RIO(object):
    def __init__(self, context, verbose=False):
        """Context-Aware brainstorm assistant

        Parameters
        ----------
        context : AgentContext
            The context to operate the RIO under
        verbose : bool
            Whether the chain should be verbose
        """
        
        prompt = RIOPromptFormatter(input_variables=["input", "entities"],
                                    output_parser=RIOOutputParser())
        self.__chain = LLMChain(llm=context.llm, prompt=prompt, verbose=verbose)

    def __call__(self, input, entities={}):
        return self.__chain.predict_and_parse(input=input, entities=entities)

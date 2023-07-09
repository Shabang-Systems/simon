"""
followup.py
Brainstorms followup questions.
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import StringPromptTemplate
from langchain.schema import BaseOutputParser
import re

from ..models import *


TEMPLATE = """
System:
Solve the task; adhere to the following, two-line output format.

```output
Problem: why the partial answer is problemantic
Follow-up: use all of the information provided to come up with a follow-up question whose answer answers the original question and which fixes the problem you outlied above
```

Here are some supporting information:
{entities}

Human:
Question: {question}
Partial Answer: {answer}

Begin!

AI:
```output
"""

class FollowupPromptFormatter(StringPromptTemplate):
    def format(self, **kwargs):
        entities = "\n".join([
            f"{key}: {value}"
            for key,value in kwargs.pop("entities").items()])
        return TEMPLATE.format(question=kwargs["question"],
                               answer=kwargs["answer"],
                               entities=entities)

class FollowupOutputParser(BaseOutputParser):
    def parse(self, str):
        str = str.strip("```output").strip("`").strip()
        regex = r"Problem\s*:\s*(.*)\nFollow-up\s*:\s*(.*)"
        match = re.search(regex, str, re.DOTALL)

        problem = match.group(1).strip("\"").strip('"').strip("`").strip()
        followup = match.group(2).strip("\"").strip('"').strip("`").strip()

        return FollowupResult(problem, followup)

class Followup(object):
    def __init__(self, context, verbose=False):
        """Context-Aware follow-up assistant

        Parameters
        ----------
        context : AgentContext
            The context to operate the RIO under
        verbose : bool
            Whether the chain should be verbose
        """
        
        prompt = FollowupPromptFormatter(input_variables=["entities", "question", "answer"],
                                         output_parser=FollowupOutputParser())
        self.__chain = LLMChain(llm=context.llm, prompt=prompt, verbose=verbose)

    def __call__(self, question, answer, entities={}):
        return self.__chain.predict_and_parse(question=question,
                                              answer=answer,
                                              entities=entities)

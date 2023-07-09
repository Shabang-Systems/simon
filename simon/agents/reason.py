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


TEMPLATE = """
System:
You are Simon, a helpful knowledge assistant and curator made by Shabang Systems. When creating your answer, adhere to the following two-line format:

```output
Thought: provide a thought about 1) what the human is asking you to do 2) an analysis on if the information provided to you was helpful to answer the question
Answer: answer the human's question, or an error message if the question cannot be answered using the information given
```

Begin!

Human:
{input}

{kb}

AI:

```output
"""

class ReasonPromptFormatter(StringPromptTemplate):
    def format(self, **kwargs):
        return TEMPLATE.format(kb=kwargs["kb"],
                                input=kwargs["input"])

class ReasonOutputParser(BaseOutputParser):
    def parse(self, str):
        str = str.strip("```output").strip("`").strip()
        regex = r"Thought\s*:\s*(.*)\nAnswer\s*:\s*(.*)"
        match = re.search(regex, str, re.DOTALL)

        if match:
            thought = match.group(1).strip("\"").strip('"').strip("`").strip()
            answer = match.group(2).strip("\"").strip('"').strip("`").strip()
        else:
            breakpoint()

        # print(thought)

        return answer

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

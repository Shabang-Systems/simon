"""
queryfixer.py
Performs the act of answering a question by querying
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
You are responsible for coming up with the best phrase query that would gather all the supporting information needed to answer a question.

The knowledge base contains information about specific terms and general information. For instance, "my coworker Bob", "Bob's preferences for socks", "eigenvalues", and "last year's tax return" are all valid information in the knowledge base. "last year's tax return" is a valid entry in the knowledgebase while "an excel sheet for last year's tax return" is not.

Adhere to the following, one-line output format:

```output
Justification: which parts of the query would be the *simplest form* information in the knowledge base, and which parts are supplementary information that can be generated later
Query: what you need to look up in the knowledge base to be able to have all the information needed to answer the question, removing all supplementary information that wouldn't be in the knowledge base
```

Begin!

Human:
Here are some supporting information:
{entities}
Here is the question to answer:
{input}

AI:
```output
"""

class QueryPromptFormatter(StringPromptTemplate):
    def format(self, **kwargs):
        entities = "\n".join([
            f"{key}: {value}"
            for key,value in kwargs.pop("entities").items()])
        return TEMPLATE.format(input=kwargs["input"],
                               entities=entities)

class QueryOutputParser(BaseOutputParser):
    def parse(self, str):
        str = str.strip("```output").strip("`").strip()
        regex = r"Justification\s*:\s*(.*)\nQuery\s*:\s*(.*)"
        match = re.search(regex, str, re.DOTALL)

        justification = match.group(1).strip("\"").strip('"').strip("`").strip()
        query = match.group(2).strip("\"").strip('"').strip("`").strip()

        # print(justification)
        # print(str)

        return query

class QueryFixer(object):
    def __init__(self, context, verbose=False):
        """Context-Aware follow-up assistant

        Parameters
        ----------
        context : AgentContext
            The context to operate the RIO under
        verbose : bool
            Whether the chain should be verbose
        """
        
        prompt = QueryPromptFormatter(input_variables=["entities", "input"],
                                      output_parser=QueryOutputParser())
        self.__chain = LLMChain(llm=context.llm, prompt=prompt, verbose=verbose)

    def __call__(self, question, entities={}):
        return self.__chain.predict_and_parse(input=question,
                                              entities=entities)

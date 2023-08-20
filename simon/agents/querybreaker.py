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
The knowledge base contains information about specific terms and general information. For instance, "my coworker Bob", "Bob's preferences for socks", "eigenvalues", and "last year's tax return" are all valid information in the knowledge base. "last year's tax return" is a valid entry in the knowledgebase while "an excel sheet for last year's tax return" is not. Pay attention to logical keywords.

You will be provided a partial slice of the human's notes and thoughts; your job is to identify what the human is actually trying to do, and convert that to a list of key terms. These terms terms should together clarify and point to the exact thing the human is trying to look for.

Also, fix the user's spelling.

Here are few examples of successful conversions:
- eigenvalue => eigenvalues
- people to visit in Bangkok => people in Bangkok, Bangkok
- Tell me about Zorbabs => Zorbabs, about Zorbabs
- What is a celender => definition of calendar 
- sweet foods that aren't vegetables => sweet foods, not vegetables, sweet foods not vegetables, foods
- I'm traveling to Singapore next week! What should I do? => Singapore, Singapore activities, singapore activities next week

Provide your output, like the example above, in a comma seperated list of keywords that would appear in the knowledge base. 

```output
query one, query two
...
```

Begin!
, visiting Bangkok
Human:
Here is the question for you to patch:
{input}

AI:
```output
""
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
        str = str.strip("`").strip("'").strip('"').strip()
        res = str.split(",")
        
        return [i.strip() for i in res]

class QueryBreaker(object):
    def __init__(self, context, verbose=False):
        """Context-Aware follow-up assistant

        Parameters
        ----------
        context : AgentContext
            The context to operate the RIO under
        verbose : bool
            Whether the chain should be verbose
        """
        
        self.__prompt = QueryPromptFormatter(input_variables=["entities", "input"],
                                             output_parser=QueryOutputParser())
        self.__chain = LLMChain(llm=context.llm, prompt=self.__prompt, verbose=verbose)

    def __call__(self, question, entities={}):
        out =  self.__chain.predict(input=question,
                                    entities=entities)
        res =  self.__prompt.output_parser.parse(out)

        return res

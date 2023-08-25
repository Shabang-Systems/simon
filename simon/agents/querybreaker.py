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
The knowledge base contains information about specific terms and general information. For instance, "my coworker Bob", "Bob's preferences for socks", "eigenvalues", and "last year's tax return" are all valid information in the knowledge base. "last year's tax return" is a valid entry in the knowledgebase while "an excel sheet for last year's tax return" is not.

You will be provided a partial slice of the human's notes and thoughts; your job is to identify what the human is actually trying to do, and convert that to a more genreal question or statement that uses only keywords that could be found in the knowledge base.

Also, fix the user's spelling.

Here are few examples of successful conversions:
- "What's an eigenvalue?" => "Eigenvalues, Eigenvalues definition"
- "Tell me about Zorbabs" => "Zorbabs"
- "What is a celender" => "calendar"
- "I'm traveling to Singapore next week! What should I do?" => "Singapore, singapore activities"
- "Who should I visit in Bangkok?" => "people I know in Bangkok, Bangkok visit"

Provide your output in this format:

```output
New, shortened statement for the database that is not a question but instead a comma-seperated list of statements:
""your full, new question/statement here.""
```

Begin!

Human:
Here is the question for you to patch:
{input}

AI:
```output
New, shortened statement for the database that is not a question but instead a comma-seperated list of statements:
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
        
        return [i.strip() for i in str.split(",")]

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

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

You will be provided a partial slice of the human's notes and thoughts; your job is to identify what the human is actually trying to look for, and convert that to a more genreal question or statement that uses only keywords that could be found in the knowledge base.

Also, fix the user's spelling.

Here are few examples of successful conversions:
- "What's an eigenvalue?" => "Eigenvalues"
- "Tell me about Zorbabs" => "Zorbabs"
- "What is a celender" => "calendar"
- "I'm traveling to Singapore next week! What should I do?" => "activites in Singapore"
- "Who should I visit in Bangkok?" => "people I know in Bangkok"

Here are some examples of things that shouldn't come up:
- "What's an eigenvalue?" should NOT be converted to "eigenvalues definition", instead it should be "eigenvalues"
- "What is the purpose of Acme" should NOT be converted to "acme purpose", instead it should be "acme"
- "Write song lyrics about the meaning of Acme" should NOT be converted to "Acme song lyrics", instead it should be "acme"
- "what are a few examples of vegetables that are healthy" should NOT be converted to "examples of vegetables that are healthy", instead it should be "healthy vegetables"

Your goal is to come up with the OBJECTS that will be helpful. If the human is asking you to do something, filter out the part that involves the request for action.

Provide your output in this format:

```output
Single noun phrase that encopsulates the question, grammar and spelling and capitalization corrected, if you can't do it type N/A here:
""your full, new question/statement here.""
```

Begin!

Human:
Here is the question for you to patch:
{input}

AI:
```output
Single noun phrase that encopsulates the question, grammar and spelling and capitalization corrected, if you can't do it type N/A here:
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
        if str.strip().lower() == "n/a":
            return None

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
        if not res:
            return None

        return list(set(res))

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

import re

from ..models import *


TEMPLATE = """
System:
You will be given the human's partial thoughts and some knowledge. Your job is to come up with salient comments which the human couldn't have possible thought of without knowing the knowledge you have. These comment should be able to be searched in the knowledgebase.

Include only information that is
1. in the Knowledge you are provided
2. which you think the human wouldn't possibly have thought of without the Knowledge you are provided

Keep everything extremely brief. Adhere to the following format.

```output
Comments: A markdown list with good, salient questions or comments the human would ask but which the human couldn't have possibly thought of without the knowledge base. These questions should be in the tone of the human, and be directly useful to search the knowledge base. This list can only ask about the information in the knowledge base, or direct extensions from it. This list can contain at *most four elements*, but should be usually kept to 2-3. They can be statements or questions. They should stand independently and not build off of each other.
```

For instance:
Question:
"I'm visiting Smithtown, what should I do?" 

Knowledge:
Title: John -- John works in Syscorp.
---
Title: Syscorp -- Syscorp is an Canadian company with headquarters in Smithtown.
---
Title: Smithtown airport instructions -- Go to Terminal 3, and turn left to hail a cab. That will be the easiest.

```output
Comments:
- Who is John from Smithtown?
- Who else can we visit at Syscorp?
- Cab hailing instructions at Smithown
```

Remember to return at most 4 results.

Question:
{input}

Knowledge:
{entities}
{kb}

Begin!

```output
Comments:"""

class RIOPromptFormatter(StringPromptTemplate):
    def format(self, **kwargs):
        entities = "\n".join([
            f"{key}: {value}"
            for key,value in kwargs.pop("entities").items()])
        return TEMPLATE.format(input=kwargs["input"], entities=entities, kb=kwargs["kb"])

class RIOOutputParser(BaseOutputParser):
    def parse(self, str) -> RIOObservation:
        str = str.strip("```output").strip("`").strip()
        # regex = r"\s*(.*)\n\n?Comments\s*:\s*(.*)"
        # match = re.search(regex, str, re.DOTALL)

        # gap = match.group(1).strip("\"").strip('"').strip("`").strip()
        str = str.strip("\"").strip('"').strip("`").strip()

        questions = [i.strip("-").strip()
                     for i in str.strip().replace("\n -", "\n-").split("\n-")
                     if i.strip() != '']

        return questions

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
        
        prompt = RIOPromptFormatter(input_variables=["input", "kb", "entities"],
                                    output_parser=RIOOutputParser())
        self.__chain = LLMChain(llm=context.llm, prompt=prompt, verbose=verbose)

    def __call__(self, input, kb="", entities={}):
        return self.__chain.predict_and_parse(input=input, kb=kb, entities=entities)

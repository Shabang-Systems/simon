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

Pay attention to the lack of knowledge the human's partial thoughts betray and fix them by coming up with good questions/comments that help the human discover that facet of knowledge.

When replying with your comments, adhere to the following format.

```output
Gap: one sentence outlining what the human showed through their partial notes that they wouldn't possibly have known without the knowledge you are provided
Comments: this is a list deliminated by a new line and ---, each element of which has two parts. In the first part, provide a good, salient question or comment the human couldn't have possibly thought of without the knowledge base that can be used by the human to directly search the knowlege base. Then, you will use ||| to seperate the two parts. The second part is 1-4 words which summarizes the overall point of your comment. 
This could repeat at most 4 times, but should be usually kept to 2-3. They can be statements or questions. They should stand independently and not build off of each other.
```

For instance:
Question:
"I'm visiting Toronto, what should I do?" 

Knowledge:
Title: John -- John works in Syscorp.
---
Title: Syscorp -- Syscorp is an Canadian company with headquarters in Toronto.
---
Title: Toronto airport instructions -- Go to Terminal 3, and turn left to hail a cab. That will be the easiest.

```output
Gap: The human wouldn't have known that John is probably in Toronto.
Comments:
John lives in Toronto. Could you please tell me more about John? ||| Visiting John
---
Syscorp is based in Toronto. What are some other people we can visit at Syscorp? ||| More on Syscorp
---
Here are some specific instructions to hailig a cab at the Minnesota airport:
1. Go to terminal 3
2. Turn left ||| Airport Instructions
```

Remember, you maybe passed a *PARTIAL* slice of your thoughts. Hence, try to guess what the human is trying to say if their text is cut off awkwardly. 

Question:
{input}

Knowledge:
{entities}
{kb}

Begin!

```output
Goal:"""

class RIOPromptFormatter(StringPromptTemplate):
    def format(self, **kwargs):
        entities = "\n".join([
            f"{key}: {value}"
            for key,value in kwargs.pop("entities").items()])
        return TEMPLATE.format(input=kwargs["input"], entities=entities, kb=kwargs["kb"])

class RIOOutputParser(BaseOutputParser):
    def parse(self, str) -> RIOObservation:
        str = str.strip("```output").strip("`").strip()
        regex = r"\s*(.*)\n\n?Comments\s*:\s*(.*)"
        match = re.search(regex, str, re.DOTALL)

        gap = match.group(1).strip("\"").strip('"').strip("`").strip()
        comments = match.group(2).strip("\"").strip('"').strip("`").strip()


        questions = [i.strip("-").strip()
                     for i in comments.strip().split("---")
                     if i.strip() != '']
        questions = [[j.strip() for j in i.split("|||")] for i in questions]

        return {
            "gap": gap,
            "comments": [{"summary": i[1],
                          "comment": i[0]} for i in questions]
        }

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

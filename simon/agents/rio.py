"""
rio.py
Brainstorming relavent tasks
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import StringPromptTemplate
from langchain.schema import BaseOutputParser

from collections import defaultdict

from nltk import sent_tokenize

import logging
L = logging.getLogger("simon")

import re

from ..models import *

TEMPLATE = """
System:
You will be given the human's partial thoughts and some knowledge. Your job is to come up with salient comments which the human couldn't have possible thought of without knowing the knowledge you have. These comment should be able to be searched in the knowledgebase.

Keep everything extremely brief. Adhere to the following format.

```output
AI Thought: I am going to make five comments which only rely on the information I am provided above now.

Comments: A markdown list with good, salient questions or comments the human would ask but which the human couldn't have possibly thought of without the knowledge base. These questions should be in the tone of the human, and be directly useful to search the knowledge base. This list can only ask about the information in the knowledge base, or direct extensions from it. This list can contain at *most five elements*, but should be usually kept to 2-3. They can be statements or questions. They should stand independently and not build off of each other.
```

For instance:
Question:
"I'm visiting Smithtown, what should I do?" 

Knowledge:
John works in Syscorp. [0] Syscorp is an Canadian company with headquarters in Smithtown. [1] Smithtown airport instructions [2] -- Go to Terminal 3, and turn left to hail a cab. That will be the easiest. [3]

```output
AI Thought: I am going to make at most five comments which only rely on the information I am provided about and which helps the user.

I'm looking for comments relavent to:
I'm visiting Smithtown, what should I do?

Here are the headline-style comments, each should be under 5 words:
- John at Syscorp [0]
- Cab hailing instructions [3]
```

Remember to return at most 5 results.

Question:
{input}

Knowledge:
{kb}

Begin!

```output
AI Thought: I am going to make at most five comments which only rely on the information I am provided above now.

I'm looking for comments relavent to:
{input}

Here are the headline-style comments, each should be under 5 words:"""


class RIOPromptFormatter(StringPromptTemplate):
    def format(self, **kwargs):
        return TEMPLATE.format(input=kwargs["input"], kb=kwargs["kb"])

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

        resource_regex = r"\[(\d+)\]"

        # collect up the extrapolation citations
        ex_citations = []
        for extrapolation in questions:
            # get the extrapolation id
            results = list(re.findall(resource_regex, extrapolation))
            if len(results) == 0:
                ex_citations.append(-1)
                continue

            for r in results:
                ex_citations.append(int(r.strip()))
                continue

        # and we now remove all the citatinos from the extrapolations
        questions = [re.sub(resource_regex, "", i).strip() for i in questions]

        return questions, ex_citations

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
        
        self.__prompt = RIOPromptFormatter(input_variables=["input", "kb"],
                                    output_parser=RIOOutputParser())
        self.__chain = LLMChain(llm=context.llm, prompt=self.__prompt, verbose=verbose)

    def __call__(self, input, kb=[]):
        # initialize the dictionary for text-to-number labeling
        # this dictionary increments a number for every new key
        resource_ids = defaultdict(lambda : len(resource_ids))

        # chunk the resource into sentences and label them
        # this is a dictionary of resource_id:kb_entry
        chunks = {k:v
                  for indx, i in enumerate(kb)
                  for k,v in [(resource_ids[j], indx)
                              for j in sent_tokenize(i["text"])]}

        # freeze and reverse the resource id dictionary
        # so this is now a dict of resource_id:text
        resource_ids = {v:k for k, v in resource_ids.items()}

        # tack the numerical labels onto the actual chunks into a big
        # context string
        # hard limit of 5500
        sentences = "".join([text+f" [{indx}]\n " for indx, text in resource_ids.items()])[:5500]

        L.debug(f"Starting brainstorm request!!!")

        output = self.__chain.predict(input=input, kb=sentences)
        res, citations = self.__prompt.output_parser.parse(output)

        # parse citations
        resources = [{"headline": headline,
                      "resource": {"quote": resource_ids[i],
                                   "chunk": kb[chunks[i]]}} for i, headline in zip(citations, res)]

        L.debug(f"All done now with brainstorm")

        return resources

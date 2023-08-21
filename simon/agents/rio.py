"""
rio.py
Brainstorming relavent tasks
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import StringPromptTemplate
from langchain.schema import BaseOutputParser
from langchain.callbacks.base import BaseCallbackHandler

from collections import defaultdict

from nltk import sent_tokenize

import logging
L = logging.getLogger("simon")

import re

from ..models import *

TEMPLATE = """
System:
You will be given the human's partial thoughts and some knowledge. Your job is to come up with salient comments which the human couldn't have possible thought of without knowing the knowledge you have. These comment should be able to be searched in the knowledgebase.

Keep everything extremely brief. You will provide a list of outputs, which contains salient questions or comments the human would ask but which the human couldn't have possibly thought of without the knowledge base. These questions should be in the tone of the human, and be directly useful to search the knowledge base. This list can only ask about the information in the knowledge base, or direct extensions from it. 

In each list element, provide a headline describing the resource you are referring the human to read, then two special tags. One tag referring to the resource, and one tag referring to the statement that the human said which prompted you to provide the resource.

For instance:
Question:
I'm visiting Smithtown. <0> what should I do? <1>

Knowledge:
John works in Syscorp. [0] Syscorp is an Canadian company with headquarters in Smithtown. [1] Smithtown airport instructions [2] -- Go to Terminal 3, and turn left to hail a cab. That will be the easiest. [3]

```output
- John at Syscorp <1> [0]
- Cab hailing instructions <0> [3]
```

Each entry in the result must not use more than 7 words, and they must not contain : or ".

You maybe provided resources that are entirely irrelavent. If so, *don't include them!* Use your best judgement to select resources and answers that will help surface unexpected information. Fact chec the resources; if something doesn't make sense, don't include it. 

You may only use each angle bracket tag *ONCE*. For instance, if one of your output lines contained <1>, you may not use <1> again. 

Question:
{input}

Knowledge:
{kb}

Begin!

```output
"""


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

        # collect up the extrapolation inputs
        citation_regex = r"<(\d+)>"
        input_citations = []
        for extrapolation in questions:
            # get the extrapolation id
            results = list(re.findall(citation_regex, extrapolation))
            if len(results) == 0:
                input_citations.append(-1)
                continue

            for r in results:
                input_citations.append(int(r.strip()))
                continue

        # and we now remove all the citatinos from the extrapolations
        questions = [re.sub(resource_regex, "", i) for i in questions]
        questions = [re.sub(citation_regex, "", i).strip() for i in questions]

        return questions, ex_citations, input_citations

# TODO the streaming API is currently really poorly designed
# so TODO make it better lol - hjl
class RIOSingleUseCallbackHandler(BaseCallbackHandler):
    def __init__(self, callback, formatter, destructor):
        self.__scratchpad = ""
        self.__callback = callback
        self.__formatter = formatter
        self.__destructor = destructor
        self.__cache = None

    def on_llm_new_token(self, **kwargs):
        try:
            self.__scratchpad += kwargs["token"]

            out = self.__formatter(self.__scratchpad)
            if out and out != self.__cache:
                self.__cache = out

                self.__callback({"output": self.__cache,
                                "done": False})
        except Exception as e:
            pass

    def on_llm_end(self, res, **kwargs):
        self.__callback({"output": self.__cache,
                         "done": True})
        self.__destructor()


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
        self.__chain = LLMChain(llm=context.reason_llm, prompt=self.__prompt, verbose=verbose)


    def __call__(self, input, kb=[], streaming=None):
        # Tokenize the sentence
        sent_ids = defaultdict(lambda : len(sent_ids))
        [sent_ids[i] for i in sent_tokenize(input)]
        sent_ids = dict(sent_ids)

        # freeze and reverse the resource id dictionary
        # so this is now a dict of resource_id:text
        sent_ids = {v:k for k, v in sent_ids.items()}

        # create the tagged input 
        tagged_input = "".join(text+f" <{indx}> " for indx, text in sent_ids.items())
            

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

        # if we are streaming, inject the streaming tools into the llm
        # and parse accordingly
        if streaming:
            L.debug(f"Streanming !!!")
            def format_callback(output):
                res, citations, inputs = self.__prompt.output_parser.parse(output)
                return [{"headline": headline,
                         "relavent_input": sent_ids[inp],
                         "resource": {"quote": resource_ids[i],
                                      "chunk": kb[chunks[i]]}} for i, headline, inp in zip(citations, res, inputs)]

            def remove_callback():
                self.__chain.llm.callbacks = [i for i in self.__chain.llm.callbacks if type(i) != RIOSingleUseCallbackHandler]
                
            # create the callback handler 
            callback = RIOSingleUseCallbackHandler(streaming, format_callback, remove_callback)

            # and bind it to the llm
            self.__chain.llm.streaming = True
            if type(self.__chain.llm.callbacks) == list:
                self.__chain.llm.callbacks.append(callback)
            else:
                self.__chain.llm.callbacks = [callback]

            self.__chain.llm.temperature = 0

            # kick that puppy into motion 
            self.__chain.predict(input=tagged_input, kb=sentences)

            # return nothing
            return
 

        output = self.__chain.predict(input=tagged_input, kb=sentences)
        res, citations, inputs = self.__prompt.output_parser.parse(output)

        # parse citations
        resources = [{"headline": headline,
                      "relavent_input": sent_ids[inp],
                      "resource": {"quote": resource_ids[i],
                                   "chunk": kb[chunks[i]]}} for i, headline, inp in zip(citations, res, inputs)]

        L.debug(f"All done now with brainstorm")

        return resources

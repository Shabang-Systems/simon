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

from ..utils.helpers import *
import threading

import logging
L = logging.getLogger("simon")

import re

from ..models import *

TEMPLATE = """
System:
You will be given the human's partial thoughts and some knowledge. Your job is to come up with salient comments which the human couldn't have possible thought of without knowing the knowledge you have. These comment should be able to be searched in the knowledgebase.

In each list element, provide a headline answering why the knowledge you are about to provide is relavent to the user, then two special tags. One tag using <> brackets referring to the statement that the human said which prompted you to provide the knowledge you are providing, and one tag using [] brackets referring to the actual resource you are providing to the user.

For instance:
Question:
I'm visiting Smithtown. <0> what should I do? <1>

Knowledge:
John works in Syscorp. [0] Syscorp is an Canadian company with headquarters in Smithtown. [1] Smithtown airport instructions [2] -- Go to Terminal 3, and turn left to hail a cab. That will be the easiest. [3]

```output
- John at Syscorp in Smithtown <1> [0]
- Cab hailing instructions for Smithtown <0> [3]
```

Each entry in the result must not use more than 7 words, and they must not contain : or ". Each entry should provide a hint to the user as to why it is relavent to their query.

Each entry should be of the EXACT SHAPE:

- short headline <a> [b]

With those tags in that order. The headline should summarize the *knowledge* you are providing (not the user input) and should also be less that 7 words. Like a seacrh engine, *RANK YOUR RESULTS*: the most relavent result should be first in your output.

You are only going to retrieve things that are relavent to the user's query, and filter out those that are useless or factually incorrect. *You maybe provided knowledge that are entirely irrelavent*. If so, *don't include them!* Use your best judgement to select knowledge and responses that will help surface unexpected information. Fact check the knowledge; if something doesn't make sense, don't include it.

You can return an empty string if you don't want to return anything.

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
    def parse(self, str):
        str = str.strip("```output").strip("`").strip()
        # regex = r"\s*(.*)\n\n?Comments\s*:\s*(.*)"
        # match = re.search(regex, str, re.DOTALL)

        # gap = match.group(1).strip("\"").strip('"').strip("`").strip()
        str = str.strip("\"").strip('"').strip("`").strip()

        questions = [i.strip("-").strip()
                    for i in str.strip().replace("\n -", "\n-").split("\n-")
                    if i.strip() != '']

        # filter for those that match the regex
        match_regex = r".* ?<(\d+)> ?\[(\d+)\]"
        questions = list(filter(lambda x:re.match(match_regex, x), questions))

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
    def __init__(self, formatter, destructor):
        self.__scratchpad = ""
        self.__formatter = formatter
        self.__destructor = destructor
        self.__cache = None
        self.__last_output = None
        self.done = False

    def blocking_next(self):
        while not self.__last_output:
            if self.done:
                break

        lo = self.__last_output
        self.__last_output = None
        return lo

    def on_llm_new_token(self, **kwargs):
        self.__scratchpad += kwargs["token"]

        out = self.__formatter(self.__scratchpad)

        if out and out != self.__cache:
            self.__cache = out
            self.__last_output = {"output": self.__cache, "done": False}

    def on_llm_end(self, res, **kwargs):
        self.__last_output = {"output": self.__cache, "done": True}
        self.done = True
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


    def __call__(self, input, kb=[], streaming=False):
        # Tokenize the sentence
        sent_ids = defaultdict(lambda : len(sent_ids))
        [sent_ids[k] for i in [sent_tokenize_d(j) for j in input.split(",")] for k in i]
        sent_ids = dict(sent_ids)

        # freeze and reverse the resource id dictionary
        # so this is now a dict of resource_id:text
        sent_ids = {v:k for k, v in sent_ids.items()}

        # create the tagged input 
        tagged_input = "".join(text+f" <{indx}> " for indx, text in sent_ids.items())
        
        if not kb:
            return

        # initialize the dictionary for text-to-number labeling
        # this dictionary increments a number for every new key
        resource_ids = defaultdict(lambda : len(resource_ids))

        # chunk the resource into sentences and label them
        # this is a dictionary of resource_id:kb_entry
        chunks = {k:v
                  for indx, i in enumerate(kb)
                  for k,v in [(resource_ids[j], indx)
                              for j in sent_tokenize_d((i["metadata"]["title"] if i["metadata"]["title"] != None else "")+" "+i["text"])]}

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
            L.debug(f"Streaming !!!")
            def format_callback(output):
                res, citations, inputs = self.__prompt.output_parser.parse(output)
                return [{"headline": headline,
                        "relavent_input": sent_ids[inp],
                        "resource": {"quote": resource_ids[i],
                                    "chunk": kb[chunks[i]]}} for i, headline, inp in zip(citations, res, inputs)]

            
            def remove_callback():
                self.__chain.llm.callbacks = [i for i in self.__chain.llm.callbacks if type(i) != RIOSingleUseCallbackHandler]
                
            # create the callback handler 
            callback = RIOSingleUseCallbackHandler(format_callback, remove_callback)

            def streaming_generator():
                while not callback.done:
                    yield callback.blocking_next()

            # and bind it to the llm
            self.__chain.llm.streaming = True
            if type(self.__chain.llm.callbacks) == list:
                self.__chain.llm.callbacks.append(callback)
            else:
                self.__chain.llm.callbacks = [callback]

            self.__chain.llm.temperature = 0


            # kick that puppy into motion 
            thread = threading.Thread(target=self.__chain.predict,
                                      kwargs={"input": tagged_input,
                                              "kb": sentences})
            thread.start()
            # return nothing
            return streaming_generator()
        

        output = self.__chain.predict(input=tagged_input, kb=sentences)
        res, citations, inputs = self.__prompt.output_parser.parse(output)

        # parse citations
        resources = [{"headline": headline,
                      "relavent_input": sent_ids[inp],
                      "resource": {"quote": resource_ids[i],
                                   "chunk": kb[chunks[i]]}}
                     for i, headline, inp in zip(citations, res, inputs)]

        L.debug(f"All done now with brainstorm")

        return resources

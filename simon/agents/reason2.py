"""
reason.py
The natural language reasoning engine.
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import BaseOutputParser

from nltk import sent_tokenize
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from ..models import *

import re

# You will be provided sources to come up with an answer. When creating your answer, adhere to the following four-element format:

SYSTEM_TEMPLATE = """
You are helping a human understand the state of a concept. They will be providing a limited question to start the discussion, and you are responsible for coming up for an answer to their specific question as well as providing them general understanding. You will be provided textual knowledge which you must refer to during your answer. At the *end* of each sentence in knowledge, there is a citation take in brakets [like so] which you will refer to.

When responding, adhere to the following format.

```output
Concept: A one-line explanation of what concept the user is talking about? Be as specific as possible.

Main Idea: A one-line thought for what's important for the user to know about the overall concept.

Answer: A one-sentence, markdown-formatted, easy to understand answer to the user's question. Keep this extremely brief. You must only use information presented in the Knowledge section to provide your answer. Use **markdown** _styles_, if appropriate. At the end of your answer, provide references to useful citation numbers in brackets found in the knowledge section. Like so: [2] [3]

Extrapolations: Help the user come up information they wouldn't have possibly thought of regarding the Concept and fill in any gaps in knowledge they have betrayed through their question by extrapolating in a markdown list. Begin each element with a three-to-five word summary of the point, then a colon, then provide some explanation in one to two sentences. These extrapolations need to be short. 
- Three to five word summary: Each list element should be a clear statement of fact which will be helpful to the user. As with before, you must put citations in brackets. [1] [4]
- Three to five word summary of the point: You can do this at most 5 times. Each element in this list should be < 10 words. [3] [5]
- ...
```

Begin!
"""

HUMAN_TEMPLATE = """
Knowledge: 
{kb}

Question:
{input}
"""

AI_TEMPLATE="""
```output
Concept:"""

class ReasonPromptFormatter(BaseChatPromptTemplate):
    def format_messages(self, **kwargs):
        return [SystemMessage(content=SYSTEM_TEMPLATE),
                HumanMessage(content=HUMAN_TEMPLATE.format(kb=kwargs["kb"],
                                                           input=kwargs["input"])),
                AIMessage(content=AI_TEMPLATE)]


class ReasonOutputParser(BaseOutputParser):
    def parse(self, str):
        str = str.strip("```output").strip("`").strip()
        regex = r"\s*(.*)\n\n?Main Idea\s*:\s*(.*)\n\n?Answer\s*:\s*(.*)\n\n?Extrapolations\s*:\s*(.*)"
        match = re.search(regex, str, re.DOTALL)

        if match:
            concept = match.group(1).strip("\"").strip('"').strip("`").strip()
            main_idea = match.group(2).strip("\"").strip('"').strip("`").strip()
            answer = match.group(3).strip("\"").strip('"').strip("`").strip()
            extrapolations = match.group(4).strip("\"").strip('"').strip("`").strip()
        else:
            return str, None, ""

        # collect up all the [citations]
        resource_regex = r"\[(\d+)\]"
        resource_ids = []
        for r in re.findall(resource_regex, str):
            resource_ids.append(int(r.strip()))

        extrapolations = [i.strip() for i in extrapolations.split("\n")]

        return {
            "headline": main_idea,
            "answer": answer,
            "extrapolations": extrapolations,
            "resources": resource_ids
        }

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
        sentences = sent_tokenize(kb)
        sentences = [j for i in sentences for j in i.split("--")]

        sentence_dict = {indx:i.strip() for indx, i in enumerate(sentences)}
        sentences = "".join([i+f" [{indx}] " for indx, i in enumerate(sentences)])

        res =  self.__chain.predict_and_parse(input=input,
                                              kb=sentences)
        # we only leave useful resources
        res["resources"] = {i:sentence_dict[i] for i in res["resources"]}

        return res


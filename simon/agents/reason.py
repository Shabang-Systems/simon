"""
reason.py
The natural language reasoning engine.
"""
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import BaseOutputParser

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)


import logging
L = logging.getLogger(__name__)

from ..models import *

import re

# You will be provided sources to come up with an answer. When creating your answer, adhere to the following four-element format:

SYSTEM_TEMPLATE = """
Provide your response as a four-section answer. Each section should be seperated by one newline. The four sections are as follows: Citation, Answer, Reasoning, and Update. Use the following format to provide your answer. The human will provide your entire knowledeg.

```output
Citation: 
- "Your first quote from the knowledge. Your quote must appear exactly as-is like it appears your knowledge. Each quote may not exceed 10 words. Use ... elipses if needed."
- "Your second quote here, it still may not exceed 10 words..."
[this can repeat N times, but they must be quoted exactly from the Knowledge: section above. You may use elipses ... to skip sections, or [brackets] to add words to ensure flow.]

Answer: Use the information above to come up with a markdown-formatted, easy to understand, brief answer to the user's question. The user doesn't like reading, so keep this clear and brief. Use **markdown** _styles_, if appropriate. Synthesize: don't just copy your citations.

Reasoning: A numbered markdown list answering three questions.
1. Does your information contain information not in the citation section. Use 5 words to justify your answer. Begin your answer with the word "Yes", or "No".
2. Very briefly explain if the answer is unclear, doesn't answer the prompt, or can benefit from clarification. Begin your answer with the word "Yes", or "No".

Update: the characters N/A, if the first words to both of your answer to the reasoning section is "No"; otherwise, provide a better question that would answer the Human's question but would also yields outputs that satisfies both of the Reasoning conditions above
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
Citation:
-"""

class ReasonPromptFormatter(BaseChatPromptTemplate):
    def format_messages(self, **kwargs):
        return [SystemMessage(content=SYSTEM_TEMPLATE),
                HumanMessage(content=HUMAN_TEMPLATE.format(kb=kwargs["kb"],
                                                           input=kwargs["input"])),
                AIMessage(content=AI_TEMPLATE)]


class ReasonOutputParser(BaseOutputParser):
    def parse(self, str):
        str = str.strip("```output").strip("`").strip()
        regex = r"\s*(.*)\n\n?Answer\s*:\s*(.*)\n\n?Reasoning\s*:\s*(.*)\n\n?Update\s*:\s*(.*)"
        match = re.search(regex, str, re.DOTALL)

        L.debug(str)

        if match:
            citation = "-"+match.group(1).strip("\"").strip('"').strip("`").strip()
            answer = match.group(2).strip("\"").strip('"').strip("`").strip()
            reasoning = match.group(3).strip("\"").strip('"').strip("`").strip()
            followup = match.group(4).strip("\"").strip('"').strip("`").strip()
        else:
            return str, None, ""


        if "n/a" in followup.lower():
            followup = None

        return answer, followup, citation

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
        return self.__chain.predict_and_parse(input=input,
                                              kb=kb)


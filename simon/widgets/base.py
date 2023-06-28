"""
base.py
Base operations for widgets
"""

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import RegexDictParser
from langchain.prompts import StringPromptTemplate
from langchain.schema import BaseOutputParser
from langchain.output_parsers.json import parse_and_check_json_markdown


from abc import ABC, abstractproperty, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union, Dict

from ..models import *

TEMPLATE = """
You are an artificial intelligence responsible for creating visually appealing presentations of information for the user. You are given a chunk of text, and you are to return a markdown JSON codeblock that will help arrange ALL of the information contained in the text into slots on a specifc graphic.

For instance, if you are given a graphic that has the slots [slot_a, slot_b, slot_c], you must return the following JSON codeblock:

```json
{{
    slot_a: "text information that should be placed in slot a",
    slot_b: "text information that should be placed in slot b",
    slot_c: "text information that should be placed in slot c",
}}
```

Today, you will be arranging the information you are provided into the following graphic: {description}. This graphic has the folllowing slots [{slot_names}].

Specifically, here are the descriptions for those slots:

{slots}

Finally, here is the information you must arrange:

{input}

```json"""

class WidgetPromptFormatter(StringPromptTemplate):
    spec: WidgetSpec

    def format(self, **kwargs):
        # join the slots' spec together
        slot_names = list(self.spec.slots.keys())

        # join the slots' spec together
        slots = []
        for key, value in self.spec.slots.items():
            slots.append(f"{key}: {value}")
        slots = "\n".join(slots)

        return TEMPLATE.format(description=self.spec.description,
                               slot_names=slot_names,
                               slots=slots,
                               input=kwargs["input"])

class SimonWidget(ABC):
    @abstractproperty
    def purpose(self):
        """The purpose of this widget, ususally stars with \"a widget to display [what does it show?]\""""
        pass

    @abstractproperty
    def slots(self) -> Dict[str, str]:
        """a dictionary containing the main slots of the widget i.e. {\"slotA\": \"description of slot A\"}, etc."""
        pass

    @property
    def spec(self):
        """the WidgetSpec of the current widget"""
        return self.__spec

    @property
    def selector_option(self):
        """Serializes information about the widget as a QuerySelectorOption"""

        return QuerySelectorOption(self.purpose,
                                   self.__class__.__name__)

    def __init__(self, context, verbose=False):
        self.__context = context
        self.__spec = WidgetSpec(self.purpose, self.slots)

        prompt = WidgetPromptFormatter(spec=self.__spec, input_variables=["input"])

        self.__chain = LLMChain(llm=context.llm, prompt=prompt, verbose=verbose)

    def __call__(self, input):
        output = self.__chain.predict(input=input)
        output_json = parse_and_check_json_markdown(output.strip("`").strip(),
                                                    [i for i in self.slots.keys()])
        return output_json

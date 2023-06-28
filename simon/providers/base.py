from abc import ABC, abstractproperty, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union

from ..models import *

class SimonProvider(ABC):
    @abstractproperty
    def purpose(self):
        """The purpose of this provider, usually starts with \"Looks up [what does it do?]\""""
        pass

    @abstractmethod
    def provide(self, input) -> Union[List[SimonProviderResponse],
                                      SimonProviderError]:
        """Takes a string input, and returns ProviderResponses"""

    def __call__(self, input):
        # get the responses
        results = self.provide(input)

        if type(results) == SimonProviderError:
            return results.error

        # and then, serialize the metadata
        metadata = [i.metadata if i.metadata else {} for i in results]
        metadata_strings = [[f"Title: {i.title}"]+[f"{key}: {val}" for key,val in j.items()] for i,j in zip(results, metadata)]
        # and actually join them into a string
        metadata_strings = [", ".join(i) for i in metadata_strings]
        # and then, formulate responses
        response_string = [f"=== {meta} === \n\n"+i.body for i, meta in zip(results, metadata_strings)]

        return "\n\n---------\n\n".join(response_string)

    @property
    def selector_option(self):
        """Serializes information about the provider as a QuerySelectorOption"""

        return QuerySelectorOption(self.purpose,
                                   self.__class__.__name__)

    


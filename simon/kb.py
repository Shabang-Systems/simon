from .models import *
from .utils.elastic import *
from .components.documents import *

from abc import ABC, abstractproperty, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union

import itertools

def dedup(k):
    """Dedpulicate an unhashable-type list (i.e. set() can't work)

    Parameters
    ---------
    k : List[any]
        The input list.

    Returns
    -------
    List[any]
        Deduplicated list.
    """

    new_k = []
    for elem in k:
        if elem not in new_k:
            new_k.append(elem)

    return new_k

class KnowledgeBase():
    """General Elastic Knowledgebase Provider

    Parameters
    ----------
    context : AgentContext
        The context with which to seed the kb.
    """

    def __init__(self, context):
        self.context = context

    def provide(self, input):
        # use both types of search to create all possible hits
        results_semantic = search(input, self.context, search_type=IndexClass.CHUNK, k=10)
        # results_keywords = search(input, self.context, search_type=IndexClass.KEYWORDS, k=2)
 
        # # we then go through to find everything similar to the results to provide
        # # the model more content
        # results_similar = [j
        #                    for i in results_semantic
        #                    for j in similar(i["id"], self.context, k=1, threshold=0.95)]


        total_text = "".join(i["text"] for i in results_semantic)

        # to prevent long contexts
        while len(total_text) > 2000 and len(results_semantic) > 2:
            results_semantic = results_semantic[:-1]
            total_text = "".join(i["text"] for i in results_semantic)

        results = results_semantic
        # breakpoint()

        if len(results) == 0:
            return SimonProviderError("We found nothing. Please rephrase your question.")

        # create chunks: list of tuples of (score, title, text with context)
        chunks = assemble_chunks(results, self.context)

        responses = [SimonProviderResponse(title, body)
                     for _, title, body in chunks]

        # remove duplicates from list of lists
        # https://stackoverflow.com/questions/2213923/removing-duplicates-from-a-list-of-lists
        responses = dedup(responses)

        if responses=="\n---\n":
            return SimonProviderError("We found nothing. Please rephrase your question.")

        return responses
        
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
        response_string = [f"{meta} -- "+i.body for i, meta in zip(results, metadata_strings)]

        return "\n--\n".join(response_string)

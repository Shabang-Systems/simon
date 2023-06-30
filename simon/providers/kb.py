from .base import *
from ..models import *
from ..utils.elastic import *
from ..components.documents import *

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

class KnowledgeBase(SimonProvider):
    """General Elastic Knowledgebase Provider

    Parameters
    ----------
    context : AgentContext
        The context with which to seed the kb.
    """

    purpose="Looks up any and all knowledge about the user's world. This includes generic factual information, technical information, or information about people and things. This is the most general provider, and should be used most liberally."

    def __init__(self, context):
        self.context = context

    def provide(self, input):
        # use both types of search to create all possible hits
        results_semantic = search(input, self.context, search_type=IndexClass.CHUNK, k=3)
 
        # we then go through to find everything similar to the results to provide
        # the model more content
        results_similar = [j
                           for i in results_semantic
                           for j in similar(i["id"], self.context, k=2, threshold=0.88)]

        results = results_semantic+results_similar
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

        return responses
        

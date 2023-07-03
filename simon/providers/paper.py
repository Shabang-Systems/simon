from .base import SimonProvider
from ..models import *

from semanticscholar import SemanticScholar

class Scholar(SimonProvider):
    """Semantic Scholar API provider"""

    purpose="Looks up the latest scientific research."

    def __init__(self):
        self.__scholar = SemanticScholar()

    def provide(self, input):
        # get location information based on the query
        papers = self.__scholar.search_paper(input, limit=4)

        # and serialize into responses to return
        return [SimonProviderResponse(papers[i]["title"], papers[i]["abstract"],
                                      {"venue": papers[i]["venue"],
                                       "citations": papers[i]["citationCount"]})
                for i in range(4)]

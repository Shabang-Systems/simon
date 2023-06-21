from .base import *
from ..models import *
from ..utils.elastic import *
from ..components.documents import *

class FakeEmail(SimonProvider):
    """Fake email provider

    Parameters
    ----------
    context : AgentContext
        The context with which to seed the kb.
    """

    purpose="Looks up the contents and addresses of previous emails sent and received by the user."

    def __init__(self, context):
        self.context = context

    def provide(self, input):
        breakpoint()
        # results = search(input, self.context)
        # if len(results) == 0:
        #     return SimonProviderError("Nothing relating to your question is found in the knowledgebase.")

        # # create chunks: list of tuples of (score, title, text with context)
        # chunks = assemble_chunks(results, self.context)
        # responses = [SimonProviderResponse(title, body, {"Score": score})
        #              for score, title, body in chunks]

        # return responses
        

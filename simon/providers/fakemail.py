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

    purpose="Looks up emails of previously sent and recieved by the user."

    def __init__(self, context):
        self.context = context

    def provide(self, input):

        return [SimonProviderResponse("Kian Email",
                                      "Hi! I'm Kian, your friend from The Nueva School. My number is 930-392-0302 if you need to reach out to me.")]

        # results = search(input, self.context)
        # if len(results) == 0:
        #     return SimonProviderError("Nothing relating to your question is found in the knowledgebase.")

        # # create chunks: list of tuples of (score, title, text with context)
        # chunks = assemble_chunks(results, self.context)
        # responses = [SimonProviderResponse(title, body, {"Score": score})
        #              for score, title, body in chunks]

        # return responses
        

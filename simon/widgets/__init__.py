from .base import SimonWidget
from .simple import *
from .people import *
from .location import *
from .misc import *

from ..models import AgentContext

def get_widget_suite(context: AgentContext):
    """get a core selection of built-in simon widgets

    Parameters
    ----------
    context : AgentContext
        the context to use to seed the widgits

    Returns
    -------
    List[SimonWidget]
        the initialized widgets
    """

    return [
        TextChunk(context),
        TextList(context),
        HeadlineDescription(context),
        ContactCard(context),
        ContactCards(context),
        Codeblock(context),
        Definition(context),
        Location(context),
        Error(context),
    ]
    


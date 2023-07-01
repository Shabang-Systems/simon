from .base import *
from ..models import *

import re
from uuid import uuid4
import requests

class Map(SimonProvider):
    """Google Maps API service handler

    Parameters
    ----------
    context : AgentContext
        The context with which to seed the kb.
    key : str
        Mapbox API Key
    """

    purpose="Looks up factual information about exact street addresses or generic local businesses \"coffee shops near me\" or \"chinese food\". This provider only has generic public information. For instance, \"best chinese food\" is a valid query for this provider, but \"Bob's favorite Chinese food place\" is *not* a valid query and should be deffered to another provider."

    def __init__(self, key):
        self.__key = key

    def __hydrate(self, query):
        return f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&inputtype=textquery&key={self.__key}"

    def provide(self, input):
        # get location information based on the query
        response = requests.get(self.__hydrate(input))
        res = response.json()

        # gets the places data
        places = res["results"]

        # serialize into title, address ("place name"), category
        serialized = [(i["name"], i["formatted_address"]+"\n"+", ".join(i["types"]),
                       {"price level": i.get("price_level", "unknown"), "rating": i.get("rating", "unknown")})
                      for i in places[:5]]

        # and serialize into responses to return
        return [SimonProviderResponse(name, details, metadata)
                for name, details, metadata in serialized]

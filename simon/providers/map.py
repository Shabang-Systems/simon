from .base import *
from ..models import *

from uuid import uuid4
import requests

class Map(SimonProvider):
    """Mapbox API service handler

    Parameters
    ----------
    context : AgentContext
        The context with which to seed the kb.
    key : str
        Mapbox API Key
    """

    purpose="Looks up exact street addresses or local businesses \"coffee shops near me\" or \"chinese food\""

    def __init__(self, key):
        self.__key = key

    def __hydrate(self, query):
        return f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json?access_token={self.__key}&fuzzyMatch=true&proximity=ip&limit=5"

    def provide(self, input):
        # get location information based on the query
        response = requests.get(self.__hydrate(input))
        res = response.json()

        # gets the places data
        places = res["features"]

        # serialize into title, address ("place name"), category
        serialized = [(i["text"], i["place_name"], i["properties"].get("category"))
                      for i in places]

        # and serialize into responses to return
        return [SimonProviderResponse(name, address+"\n"+info) for name, address, info in serialized]

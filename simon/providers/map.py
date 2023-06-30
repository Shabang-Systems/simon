from .base import *
from ..models import *

import re
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

    purpose="Looks up factual information about exact street addresses or generic local businesses \"coffee shops near me\" or \"chinese food\""

    def __init__(self, key):
        self.__key = key

    def __hydrate(self, query):
        return f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json?access_token={self.__key}&fuzzyMatch=true&proximity=ip&limit=5"

    def __clean(self, query):
        """removes irrelavent words

        mapbox's API doesn't have very good contextual search;
        therefore, we need to clean out a lot of the common "useless"
        phrases to ensure a good quality search

        Parameters
        ----------
        query : str
            the input query

        Returns
        -------
        str
            the cleaned query
        """

        query = query.lower().replace("in the area", "")
        query = query.replace("local", "")
        query = query.replace("good", "")
        query = query.replace("bad", "")
        query = query.replace("nearby", "")
        query = query.replace("near me", "")

        return query.strip()
        

    def provide(self, input):
        # get location information based on the query
        response = requests.get(self.__hydrate(self.__clean(input)))
        res = response.json()

        # gets the places data
        places = res["features"]

        # serialize into title, address ("place name"), category
        serialized = [(i["text"], i["place_name"], i["properties"].get("category", ""))
                      for i in places]

        # and serialize into responses to return
        return [SimonProviderResponse(name, address+"\n"+info) for name, address, info in serialized]

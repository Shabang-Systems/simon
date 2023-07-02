"""
location.py
Widgets focusing on representing locations such as restaurants or shops
"""

from .base import SimonWidget

class Location(SimonWidget):
    purpose = "a widget that presents a physical location in the world"
    slots = {
        "name": "the name of the establishment",
        "description": "description of what is at the location",
        "purpose": "one to two word purpose of the establishment such as restaurant, shopping mall, apartment, etc.",
        "address": "address or coordinates to the location",
        "phone": "phone number of the location, if included, or just the letters N/A",
        "email": "email address of the location, if included, or just the letters N/A",
        "other": "other information, seperated as a markdown list delineated by -. If no information exists, provide just the letters N/A.",
    }


class Locations(SimonWidget):
    purpose = "a widget that presents a list of multiple physical locations in the world"
    slots = {
        "name": "names of locations, listed as a markdown list delinated by newlines and -",
        "number": "number of locations presented",
        "purpose": "one to two word purpose of the group of locations, such as restaurant, shopping mall, apartment, etc.",
        "address": "addresses of the locations, listed as a markdown list delinated by newlines and -",
        "phone": "phone numbers of the locations, listed as a markdown list delinated by newlines and -, if included, or just the letters N/A",
        "email": "email addresses of the locations, listed as a markdown list delinated by newlines and -, if included, or just the letters N/A",
        "other": "other information, seperated as a markdown list delineated by -. If no information exists, provide just the letters N/A. Seperate information about each different location with two new lines.",
    }


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
        "other": "other contact information, seperated as a markdown list delineated by -. If no information exists, provide just the letters N/A.",
    }


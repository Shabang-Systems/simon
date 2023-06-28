"""
people.py
Widgets focusing on presenting information about people.
"""

from .base import SimonWidget

class ContactCard(SimonWidget):
    purpose = "a widget that presents a person's description and contact information"
    slots = {
        "name": "full name of the person",
        "email": "email of the person, if included, or just the letters N/A",
        "phone": "phone number of the person, if included, or just the letters N/A",
        "description": "short description of the person",
        "title": "the work/school title and location of the person, like \"professor of biology, UCSC\"",
        "other": "other contact information, seperated as a markdown list delineated by -. If no information exists, provide just the letters N/A.",
    }


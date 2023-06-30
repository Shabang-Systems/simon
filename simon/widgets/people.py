"""
people.py
Widgets focusing on presenting information about people.
"""

from .base import SimonWidget

class ContactCard(SimonWidget):
    purpose = "a widget that presents a person's contact information"
    slots = {
        "name": "full name of the person",
        "email": "email of the person, if included, or just the letters N/A",
        "phone": "phone number of the person, if included, or just the letters N/A",
        "title": "the work/school title and location of the person, like \"professor of biology, UCSC\"",
        "organization": "what organization this person works in/with, like UCSC, or N/A",
        "other": "other contact information, seperated as a markdown list delineated by -. If no information exists, provide just the letters N/A.",
    }


class ContactCards(SimonWidget):
    purpose = "a widget that presents contact information about multiple people"
    slots = {
        "number": "number of people presented",
        "name": "full names of the people, seperated by commas",
        "relation": "how this group of people are related",
        "email": "emails of the people, seperated by commas, if included, or just the letters N/A",
        "phone": "phone numbers of the people, seperated by commas, if included, or just the letters N/A",
        "organizations": "which organizations are these people in, seperated by commas, or N/A",
        "other": "other contact information, seperated as a markdown list delineated by -. If no information exists, provide just the letters N/A.",
    }



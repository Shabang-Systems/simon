"""
simple.py
A collection of simple widgets.
"""

from .base import SimonWidget

class TextChunk(SimonWidget):
    purpose = "a simple widget which presents a chunk of text"
    slots = { "text": "the main chunk of text" }

class TextList(SimonWidget):
    purpose = "a simple widget which presents a list of text"
    slots = { "list": "a markdown list of text with the main point of the text, with each point on a row delinated by -" }

class HeadlineDescription(SimonWidget):
    purpose = "a simple widget with a main headline with detailed description"
    slots = {
        "headline": "a main tagline/summary of the text",
        "details": "important details, arranged as a markdown list deliminated by -"
    }

class Codeblock(SimonWidget):
    purpose = "a simple widget that presents a chunk of code with some explanation"
    slots = {
        "codeblock": "the raw source code, with ample comments",
        "explanation": "human readable text explaining the text",
        "language": "programming language to syntax highlight the codeblock with"
    }







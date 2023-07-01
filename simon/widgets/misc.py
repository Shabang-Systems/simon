"""
misc.py
A set of fun widgets that's pretty fun, but probably isn't that interesting.
"""

from .base import SimonWidget

class Definition(SimonWidget):
    purpose = "a widget to provide the definition or meaning of a key word"
    slots = {
        "term": "the word to be defined",
        "type": "one-word summarization for what type of definition this is; for obscure vocabulary, this could be the part of speech of the word. For others, it could be the subject area the term belongs to.",
        "definition":"the definition of the term",
        "examples":"A markdown list containing examples of instances of the term, or the term being used. Delineate each example with -, end each example witha newline."
    }

class Codeblock(SimonWidget):
    purpose = "a widget that presents a chunk of code with some explanation"
    slots = {
        "codeblock": "the raw source code, with ample comments",
        "explanation": "human readable text explaining the text",
        "language": "programming language to syntax highlight the codeblock with"
    }

class Error(SimonWidget):
    purpose = "when the AI did not answer the question, or doesn't have enough info, use this widget. When the prompt starts with \"I'm sorry...\", this is usually a good choice."
    slots = {
        "error": "the problem that the AI is experiencing",
        "action": "what the AI wants the humans to reply with in order to resolve the problem",
    }







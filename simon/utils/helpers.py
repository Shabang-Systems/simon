import nltk
from nltk import sent_tokenize

import logging
L = logging.getLogger("simon")


def sent_tokenize_d(sentences):
    """Sentence tokenize `sentences`, or download punkt and then do it

    Parameters
    ----------
    sentences : str
        Sentences to tokenize.

    Returns
    -------
    List[str]
        The tokenized sentences.
    """

    try:
        return sent_tokenize(sentences)
    except LookupError:
        nltk.download("punkt")
        return sent_tokenize(sentences)



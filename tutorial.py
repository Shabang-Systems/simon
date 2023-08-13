"""
Hello! Welcome to Simon!

This file demonstrates some common patterns that you should be aware of while
working with the Simon library. We recommend these patterns as you develop
your own solutions with Simon.

We recommend you read this file from top to bottom, as effectively a quick
start guide to Simon's API.

    Copyright (C) 2023  Shabang Systems, LLC

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

### 0: Setup
# We are only setting up logging here, making Simon extremely verbose while
# muting the warning of most everything else.
# When you are debugging with Simon, this is the recommended verbosity.

import logging as L

LOG_FORMAT = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
L.basicConfig(format=LOG_FORMAT, level=L.WARNING)
L.getLogger('simon').setLevel(L.DEBUG)

# You should have your .env file and elastic instance set up accordingly.
# if you have not done so, follow instructions in README.md to get started.

# we now import the package
import simon

### 1: Simon Setup
# Your credentials are stored in an object named `AgentContext`, which most
# of every Simon utility requires in its constructor. This identifies you
# as a user, connects to the Elastic datastore, and configures the appropriate
# language (and otherwise) models for use by Simon's processes.
#
# So, to use Simon, you must create such an `AgentContext`. If you 
# followed the quick-start guide in the README of this repo,  Simon can read
# the .env file you have setup already to get your context easily.

context = simon.create_context("test-uid") # the UID here is an arbiturary string, think about it like database tables.
                                            # Data stored in `AgentContext`s belonging to one UID are not accessible by
                                            # Simon operations initialized with a context belonging to another UID.
# Note that this quickstart function takes a lot more options to directly,
# if you don't want to set up a .env file. If you have an .env file, the example above
# is enough to get you off and running.
# 
# Here are the advanced options:
#
# >>> context = create_context(uid, openai_key, es_config)
# 
# where, `openai_key` is an OpenAI API key, and `es_config` is an ElasticSearch connection dict (the
# arguments to ElasticSearch).
# If you would like *EVEN* more control over your context (how Elastic is connected to exactly,
# what language models to use, what temperatures, etc.), you can feel free to construct your own
# AgentContext object
#
# >>> context = simon.AgentContext(llm, reasoning_llm, embedding_model, elasticsearch_instance, uid)
#
# where, the llms are `langchain.llm.LLM` objects, the embedding model `langchain.embeddings.BaseEmbedding`
# elastic search an `ElasticSearch` object, and uid the same idea as before.

### 2: Datastore
# Simon manages its data with an object named Datastore:

ds = simon.Datastore(context)

# You can use this object to perform a variaty of functions. The most simple
# and directly useful of which is to make Simon parse and remember a piece of
# information located in a document on the internet.
#
# You pass this function an URL (PDF, png, or website are all fine, we can OCR)
# and a "title" identifying the document. 

doc_hash = ds.store("https://example.com", "Example Website")

# This function returns a hash identifying the document, which is used universally
# to identify this exact text (i.e., if a different URL served the same text
# it will have the same hash).
#
# Perhaps unsuprisingly, you can forget this document you just created from Simon's
# memory by

ds.delete(doc_hash)

# There are a lot more cool things you can do with a Datastore, but you can read
# all about it in the documentation.
#
# If you use the store function introduced above, however, you will get a big
# warning to use a custom ingestor from `simon.ingestion` instead of .store.
# You see, the store function above is very constraining: it OCRs a document on
# the public internet. Which... I guess its fine for quickly doing that, but there's
# a lot more things to read than single docs on the internet. To deal with those,
# introducing...

### 3: Ingesters
# Simon makes available a suite of ingesters to read all sorts of resources.
# To replicate the example store operation above using the ingester API:

from simon.ingestion import OCRIngester
ingester = OCRIngester(context)
ingester.ingest_remote("https://example.com", "Example Website")

# You can look through the rest of the ingestion documentation for other
# fun ingestors to use. OCRIngester can use .ingest_file to OCR and ingest a local
# file as well!
# A sneak peak of others:
# - `TextFileIngester`, which reads a text file either from your local machine or
#    AWS S3
# - `OCRIngester`, which secretly Parses/Reads/OCRs (last ditch) your local or remote
#   (on HTTP) document
# and, my favourite, `JSONIngester`, which programatically maps the fields of a JSON to documents.
#
# Here's an example of indexing @jemoka's notes (how's that for self-promotion?):

from simon.ingestion import JSONIngester
from simon import JSONMapping, StringMappingField, MappingTarget

ingester = JSONIngester(context)
ingester.ingest("https://www.jemoka.com/index.json", JSONMapping([StringMappingField("permalink", MappingTarget.SOURCE),
                                                                  StringMappingField("contents", MappingTarget.TEXT),
                                                                  StringMappingField("title", MappingTarget.TITLE)]))

### 4: Search
# Ok, but all that talk of ingestion is nothing if not for the main event. Search!
# That's, well, the whole point of Simon. To get started with Search, we need
# to first create a Search object:

search = simon.Search(context)

# There are four types of search one can do. The most powerful, and the big event
# of Simon is the `query` type search

result = search.query("visiting Minnisoda")

# You will note that I didn't pass an explicit "question" to Simon query. You can
# of course, but Simon is designed to siphon information and surface anything
# useful from any amount of text you have: which maybe very little! So, when we
# say "query" we do mean that---just pass any bit of text you have, and query!
#
# You should explore the result object a little. It is a Python dict with three keys
# `["answer", "answer_resources", "search_results"]`. The answer is a dicrect LLM
# answer to your query, and the other values will include the specific chunk that
# supports the LLM's answers. `search_results` provides itemized search results
# a la any other search platform, with headlines generated by the LLM.

# A second, common supporting search is a `brainstorm` type search. This type of search
# provides not an *answer*, but provides some salient questions which could
# be answered by the query function. It is intended to happen frequently in the
# background, allowing the end user to be fed a constant stream of possibly
# salient queries.

questions = search.brainstorm("visiting Minnisoda")

# Again. No need to pass a complete chunk of text.

# The third type of search is a regular document semantic search; this works like
# any other normal search engine: pass a sentence/keyword, and get documents
# and the parts that are most relavent:

results = search.search("visiting Minnisoda")

# Finally, there is a function for text-based search on *TITLES* only of the
# indexed documents. This is meant to quickly recall what is in the databse.
# this result is the only result that is *lexical*, NOT *semantic*. This means
# that this is really only suitable for quick autocomplete for an UI experience.

results = search.autocomplete("linear ma")

### 5: Prologue and Scripts
# Some scripts are available at the top level of https://github.com/Shabang-Systems/simon/
# They are meant to be helpful utilities with their own CLI interface to maange
# a Simon instance. Consult them to get started with setting up your instance.
#
# Good luck! 


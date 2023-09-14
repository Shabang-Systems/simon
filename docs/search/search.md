# Overview

Most common search requests are fulfilled using the search tool:

```python
import simon

s = simon.Search(context)
```

There are three main types of searches you can perform, each with increasing LLM/algorithmic complexity and time output takes to generate.

1. Simple semantic search
2. Text-based resurecommendation
3. Full search with LLM answering 

It is important to note that, because all three search processes uses the same prefetch system, [streaming the output](./streaming.md) will result in methods 2 and 3 taking the same time to yield the first search result as method 1.

## Simple Semantic Search
This is the most general and the quickest search mechanism out of the suite of searches with Simon. It only performs two steps: 1. linguistic and intent cleanup 2. semantic search

That is, this tool uses no recommendation or relevant passage extraction.

To do this:

```python
result = s.search("your query")
```

The result takes the following schema:

```json
[
    {
        "text": str - chunk of text that is relavent,
        "metadata": {
            "source": Optional[str] - the source you provided during ingest, or null,
            "hash": str - string hash of the resource, used for deletion/edit,
            "title": Optional[str] - the title you provided during ingest, or null
        } 
    },
    ... [sorted by relavence] ...
]
```

This simple semantic search is only recommended if downstream processing/filtering is applied. For instance, for a simple text highlight application, this search technique would suffice.

As the query mechanism returns the top ~20 most relavent results---no matter their degree of relevance---this function will always return results as long as there are data in ingested.

## Text-based recommendation ("Brainstorm")
In addition to the cleanup and search process of Simple Semantic search, the recommendation engine has a LLM layer which ensures that the returned results are relavent to your search query. It is intended to recommend search results based on the input text, and it will perform matching between relavent areas of your INPUT and OUTPUT

You can use this to build a recommendation engine! Ingest some product info, pass the user's search query, and see it run.

To do this type of search:

```python
result = s.brainstorm("your query that can be up to 200 words here")
```

And the result looks like this:

```json
[
    {
        "headline": str - LLM generated headline,
        "relavent_input": str - quote from your INPUT that motivated the result,
        "resource": {
            "quote": str - quote from `chunk.text` below that is relavent and which matched with `relavent_metadata`,
            "chunck": {
                "text": str - chunk of text that is relavent,
                "metadata": {
                    "source": Optional[str] - the source you provided during ingest, or null,
                    "hash": str - string hash of the resource, used for deletion/edit,
                    "title": Optional[str] - the title you provided during ingest, or null
                } 
            }
        }
    },
    ... [sorted by relavence] ...
]
```

If no relevant results are found, an empty array will be returned.

## Full LLM search + QA
This step is a classic retrial-augmented generation, with a search result spin: LLM answer, extractive answering, and search results. 

To do this type of search:

```python
result = s.query("write a rap about this thing I want to search")
```

And the result looks like this:

```json
{
    "answer": "llm's answers to your queries [2], along with numerical source tags [3]."
    "search_results" : [
        {
            "headline": str - LLM generated headline,
            "resource": {
                "quote": str - quote from `chunk.text` below that is relavent and which matched with `relavent_metadata`,
                "chunck": {
                    "text": str - chunk of text that is relavent,
                    "metadata": {
                        "source": Optional[str] - the source you provided during ingest, or null,
                        "hash": str - string hash of the resource, used for deletion/edit,
                        "title": Optional[str] - the title you provided during ingest, or null
                    } 
                }
            }
        },
        ... [sorted by relavence] ...
    ]
}
```


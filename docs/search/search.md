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
This is the most general, and the quickest, search out of the suite for Simon. This 


## Text-based recommendation


## Full LLM search + QA

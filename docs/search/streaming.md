# Streaming Search Results

Simon runs all of its search requests on a separate thread. Therefore, the search results all can be streamed in with traditional (i.e. non-async) generators.

Two of Simon's three search modes support streaming:

1. [text-based recommendation](./search.md#text-based-recommendation-brainstorm)
2. [LLM search and QA](./search.md#full-llm-search-qa)

In order to stream the search results, pass `True` to an optional keyword argument available to the function of those two searches.

```python
# for recommendation mode
result_generator = s.brainstorm("hello I have a question", streaming=True)
# for LLM search mode
result_generator = s.query("answer my question", streaming=True)
```

After which, the generator will return each new chunk containing the *ENTIRE ANSWER thus far* (i.e. unlike usual generators, the results here are not cumulative).

For `s.brainstorm`, new chunks get sent to the generator on each result identified. For, `s.query`, new chunks get sent to the generator on each result identified as well as each 2-3 new tokens for the answer. See the demo available [on "What" section of the home page](/) for an example of what this looks like.

To actually use the generators:

```python
# this doesnt' block
result_generator = s.brainstorm("hello I have a question", streaming=True)
# block until the first result
res = next(result_generator)
# block until the second result
res = next(result_generator)

# ... and so on
```

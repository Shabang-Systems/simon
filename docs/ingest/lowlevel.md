# Custom/Bulk Ingestion
This document is aimed to dive a little bit deeper into how Simon ingestion works, and provide you some opportunities to customize how it works yourself. **Please ensure that you are familiar with the contents of [the Datastore API](./store.md)** before reading this guide. Usually, we recommend using the `Datastore` API instead of the custom API here unless you have a specific reason to use this API (parallelization, custom cleanup, etc.).

If you do, let's get started.

## Concept
Low-level ingestion in `Simon` works in three steps:

1. Parsing: turning PDF/text/webpage you wish to ingest into `simon.ParsedDocument`
2. (optional) Cleaning: `simon.ParsedDocument` gets squished around as needed to ensure optimal search results
3. Indexing: `simon.bulk_index([list, of, parseddocuments], context)`

Especially for large ingestion jobs, we recommend having one worker perform tasks `1` and `2`, then use a queue to hand cleaned `simon.ParsedDocument`s off to a bunch of parallel workers performing `simon.bulk_index`.

## Parsing
`Simon` has three base parsing tools to help you easily create `simon.ParsedDocument`.

```python
# our tools
from simon import parse_text, parse_tika, parse_web

# parsing raw text
doc = parse_text()
```

## Cleaning

### Anatomy of a `simon.ParsedDocument`

### Actual Cleaning Recs

## Indexing
haha

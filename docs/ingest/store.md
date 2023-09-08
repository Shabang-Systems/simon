# Overview
Ingestion is the process by which you get data in and out of Simon.

## Data Store
The `Datastore` object is the high-level API by which you can manage the data you have placed in Simon.

```python
import simon

# context = simon.create_context(...)

# Create a data handler
ds = simon.Dataspore(context)
```

### Storing Data
`Datastore` Provides three main ways to store data: storing local files, storing remote files, or storing raw text.

```python
# storing a remote webpage (or, if Java is installed, a PDF/PNG)
hash = ds.store_remote("https://en.wikipedia.org/wiki/Chicken", 
                       title="Chickens",
                       source="{metadata: can go here}")

# storing a local file (or, if Java is installed, a PDF/PNG)
hash = ds.store_file("/Users/test/file.txt", 
                     title="Test File",
                     source="{metadata: can go here}")

# storing some text
hash = ds.store_text("Hello, this is the text I'm storing.", 
                     title="Title of the Text", 
                     source="{metadata: can go here}")
```

Each of the store functions take some text body to store as the first argument, and optional arguments  `title` and `source` to identify the text. 

For each of these functions, the default `title` is `None`, while the default `source` is the URL/path where the document came from.

While `title` and `source` are both strings, they have different uses as [outlined below](#title-vs-source).

Each of the `store_*` functions return a string hash uniquely identifying the document. If two documents contain identical text (despite coming from different sources), they will have the same hash and *will not be indexed twice*.

### Deleting Data
To delete a document, pass your Datastore object the hash of the document you wish to delet.

```python
# hash = ds.store_text(...)

# delete the document identified by `hash`
ds.delete(hash)
```

Most of the search facilities of Simon will also give you the `hash` of the document it returns as a result, so you don't have to database the hash separately.

## `title` vs `source`
`title` is given to the search engine and LLM to be indexed and reasoned about; `source` is a metadata field only given back to you to help you carry additional info.

Meaning, if you want something *search-able*, it cannot be placed in the `source` field as it won't be analyzed. Alternatively, if you want hold some info in the database which won't be helpful to the search algorithm, feel free to leave it in `source`.

We have three best-practice recommendations:

1. Leave anything not semantically indexable (checksums, URLs, etc.) in the `source` field
2. Feel free pack the `title` field with keywords to help the semantic indexing, and leave the actual document title in `source`
3. We recommend making `source` a JSON encoded string

## Advanced Concepts
Instead of ingesting a single document, a single webpage, etc. using `Datastore`, you can have deep customizations into the search functionality of Simon by changing how your documents are indexed. 

Especially: if you are ingesting more than 1G of documents, we recommend you **not** use `Datastore`. 

Head on on over to the [custom ingestion](./lowlevel.md) document to learn more.

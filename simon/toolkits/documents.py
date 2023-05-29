# langchain stuff
from langchain.tools import BaseTool
from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import hashlib

# mmm
import os
from typing import List, Dict

# tika
from tika import parser

# dataclasses
from dataclasses import dataclass

# constants to identify the pdffigures executable
FILEDIR = os.path.dirname(os.path.abspath(__file__))
# path to java
# TODO change this at will or put in .env 
JARDIR = os.path.abspath( 
    os.path.join(FILEDIR, "../../opt/pdffigures2.jar"))
JAVADIR = os.path.realpath(shutil.which("java"))

@dataclass
class TikaDocument:
    main_document: str
    paragraphs: List[str]
    hash: str
    meta: Dict

def parse_document(uri) -> TikaDocument:
    # parse data
    parsed = parser.from_file(uri)
    meta = {
        "source": parsed["metadata"]["resourceName"],
        "title": parsed["metadata"].get("pdf:docinfo:title"),
    }
    # clean the chunks
    parsed_chunks = [i.replace("\n"," ").replace("  ", " ").strip()
                     for i in parsed["content"].split("\n\n") if i != '']
    # and also create the bigger document
    parsed_text = " ".join(parsed_chunks)
    # hash the text
    hash = hashlib.sha256(parsed_text.encode()).hexdigest()

    # return!
    return TikaDocument(parsed_text, parsed_chunks, hash, meta)

def store(es:Elasticsearch, doc:TikaDocument, embedding:Embeddings, user:str):
    """Utility to stored parsed document.

    Parameters
    ----------
    es : Elasticsearch
        Elastic search instance used to store the data.
    doc : TikaDocument
        The document to store into elastic.
    embedding : Embeddings
        Text embedding model to use.
    user : str
        The UID.
    """
    embedded = embedding.embed_documents(doc.paragraphs)
    docs = [{"embedding": a,
             "text": b}
            for a,b in zip(embedded, doc.paragraphs)]
    update_calls = [{"_op_type": "index",
                     "_index": "simon-docs",
                     "user": user,
                     "metadata": doc.meta,
                     "hash": doc.hash,
                     "doc": i} for i in docs]
    bulk(es, update_calls)

def _seed_schema(es:Elasticsearch, dim=1546):
    """Hidden function to seed the index.

    Parameters
    ----------
    es : Elasticsearch
        Elastic search instance used to store the data.
    dim : int
        The dimension of the output.
    """
    es.indices.create(index="simon-docs", mappings={"properties": {"doc.embedding": {"type": "dense_vector",
                                                                                     "dims": 1536,
                                                                                     "similarity": "cosine",
                                                                                     "index": "true"}}})


def extract_figures(target):
    """Extract figures from PDF file with pdffigures2.

    Parameters
    ----------
    target : str
        The file to get figures from.

    Returns
    -------
    list
        A list dictionaries containing figures, their captions, and a numpy array for the figure.
    """

    # get full path of target
    target_path = os.path.abspath(target)

    # store temporary directory
    wd = os.getcwd()
    # create and change to temporary directory
    with TemporaryDirectory() as tmpdir:
        # change into temproary directory and extract figures
        os.chdir(tmpdir)
        subprocess.check_output(f"java -jar {JARDIR} -g meta -m fig {target_path} -q", shell=True)

        # read the metadata file
        meta_path = glob("meta*.json")[0]
        with open(meta_path, 'r') as df:
            meta = json.load(df)

        # open each of the images as numpy
        for figure in meta["figures"]:
            img = Image.open(figure["renderURL"])
            figure["render"] = np.array(img)
            img.close()

    # change directory back
    os.chdir(wd)

    return meta["figures"]

doc = parse_document("../blagger/data/diarization.pdf")
es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))


# es.indices.delete(index="simon-docs")
_seed_schema(es)
store(es, doc, embedding, UID)

em1 = embedding.embed_query("What is the best model for speech diarization?")
em2 = embedding.embed_query("How does this model perform?")
em3 = embedding.embed_query("diarization model performance")

results = es.search(index="simon-docs", knn={"field": "doc.embedding",
                                             "query_vector": em2,
                                             "k": 5,
                                             "num_candidates": 800})

results["hits"]["hits"][0]["_source"]["doc"]["text"keys()



tmp.paragraphs[14]

ELASTIC

ElasticSearchBM25Retriever.

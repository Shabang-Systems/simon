from dataclasses import dataclass
from langchain.embeddings.base import Embeddings
from langchain.llms.base import LLM
from elasticsearch import Elasticsearch
from typing import List, Dict
from enum import Enum

@dataclass
class AgentContext:
    llm: LLM
    embedding: Embeddings
    elastic: Elasticsearch
    uid: str


@dataclass
class ParsedDocument:
    main_document: str
    paragraphs: List[str]
    hash: str
    meta: Dict

class IndexClass(Enum):
    CHUNK = "simon-paragraphs"
    FULLTEXT = "simon-fulltext"



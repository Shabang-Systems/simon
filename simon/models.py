from dataclasses import dataclass
from langchain.embeddings.base import Embeddings
from langchain.llms.base import LLM
from elasticsearch import Elasticsearch

@dataclass
class AgentContext:
    llm: LLM
    embedding: Embeddings
    elastic: Elasticsearch
    uid: str


from dataclasses import dataclass
from langchain.embeddings.base import Embeddings
from langchain.llms.base import LLM
from elasticsearch import Elasticsearch
from typing import List, Dict, Optional
from enum import Enum
from abc import ABC, abstractmethod

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
    CHUNK = 0
    KEYWORDS = 1
    FULLTEXT = 2

class DataType(Enum):
    JSON = 0

class MappingTarget(Enum):
    TITLE = "title"
    SOURCE = "source"
    TEXT = "text"

@dataclass
class MappingField:
    src: any
    dest: MappingTarget

@dataclass
class Mapping:
    mappings: List[MappingField]

    def encode(self):
        return {res.src:res.dest.value for res in self.mappings}

    def check(self):
        targets = [i.dest for i in self.mappings]
        assert MappingTarget.TEXT in targets, "Text target not found in mapping."

@dataclass
class StringMappingField(MappingField):
    src: str
    dest: MappingTarget
    
@dataclass
class JSONMapping(Mapping):
    mappings: List[StringMappingField]

@dataclass
class QuerySelectorOption:
    info: str
    id: str

    def __hash__(self):
        return hash((self.info, self.id))

@dataclass
class SimonProviderResponse:
    title: str # the "title" of an article == Title: [here] ==
    body: str # the body text which is passed to the model
    metadata: Optional[object]=None # any other object metadata, which could be none

@dataclass
class SimonProviderError:
    error: str # the error that is exposed directly to the model


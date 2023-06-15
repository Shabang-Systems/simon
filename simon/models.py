from dataclasses import dataclass
from langchain.embeddings.base import Embeddings
from langchain.llms.base import LLM
from elasticsearch import Elasticsearch
from typing import List, Dict
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
    CHUNK = "simon-paragraphs"
    FULLTEXT = "simon-fulltext"

class MediaType(Enum):
    DOCUMENT = 0
    WEBPAGE = 1

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

class SimonToolkit(ABC):

    @property
    @abstractmethod
    def prefix(self):
        """All tools with this toolkit should have this prefix"""
        pass

    @property
    @abstractmethod
    def tools(self):
        """Returns the tools that is in this toolkit"""
        pass



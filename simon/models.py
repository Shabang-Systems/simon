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

class MediaType(Enum):
    DOCUMENT = 0
    WEBPAGE = 1
    JSON = 2

class MappingTarget(Enum):
    TITLE = "title"
    SOURCE = "source"
    TEXT = "text"

# Engineered at 12AM, future jack excuse me

@dataclass
class MappingField:
    src: any
    dest: MappingTarget

@dataclass
class Mapping:
    mappings: List[MappingField]

    def encode(self):
        return {res.src:res.dest.value for res in self.mappings}

@dataclass
class StringMappingField(MappingField):
    src: str
    dest: MappingTarget
    
@dataclass
class JSONMapping(Mapping):
    mappings: List[StringMappingField]


# JSONMapping([StringMappingField("tmp", MappingTarget.SOURCE)]).encode()



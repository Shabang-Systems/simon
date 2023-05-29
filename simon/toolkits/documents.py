# langchain stuff
from langchain.tools import BaseTool
from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document

# tika
from tika import parser

class TikaLoader(BaseLoader):
    def __init__(self, file_path:str):
        self.parsed = parser.from_file(file_path)

    def lazy_load(self):
        for i in self.parsed["content"].split("\n\n"):
            if i != '':
                yield Document(page_content=i.replace("\n",""),
                               metadata=self.meta)

    @property
    def meta(self):
        return {
            "source": self.parsed["metadata"]["resourceName"],
            "title": self.parsed["metadata"].get("pdf:docinfo:title"),
        }

    def load(self):
        return list(self.lazy_load())


# class DocumentReader
# class DocumentMemorySearch


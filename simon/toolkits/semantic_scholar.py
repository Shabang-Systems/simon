# langchain
from langchain.tools import BaseTool
from langchain.agents.agent_toolkits.base import BaseToolkit

# semanticscholar
from semanticscholar import SemanticScholar

# sleep time
import time

SCHOLAR = SemanticScholar()

class SemanticScholarSearch(BaseTool):
    name = "semantic_paper_search"
    description = "Use this tool to search for research papers based on only keywords would appear in their titles. Use this tool more than the arxiv tool if possible."

    def _run(self, query: str, run_manager = None) -> str:
        # no fucking idea why
        while True:
            try:
                # get paper
                papers = SCHOLAR.search_paper(query, limit=5)
                break
            except KeyError:
                return "This broke things, it is not your fault. Try rephrasing your question but say the same thing."
        # combine into results
        paper_blurbs = [f"paperId: {p.paperId}\ntitle: {p.title}\ncitation count: {p.citationCount}\ninfluential citations: {p.influentialCitationCount}" for p in papers[:5]]
        # return
        return "\n".join(paper_blurbs).strip()

    async def _arun(self, query: str, run_manager = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
    
class SemanticScholarRead(BaseTool):
    name = "semantic_paper_read"
    description = "Gets information about a paper based on its paperId."

    def _run(self, query: str, run_manager = None) -> str:
        engine = SemanticScholar()
        # get only the paperid part
        query = query.split(":")[-1].strip()
        query = query.split("(")[0].strip()
        # get paper ID
        try: 
            p = SCHOLAR.get_paper(query)
        except:
            return "Provide no other descriptions like parentheses, title of the paper, additional information except for the exact paperId as the action input."
        # return result
        return f"""
title: {p.title}
venue: {p.venue}
url: {p.url}
year: {p.publicationDate}
citation count: {p.citationCount}
influential citations: {p.influentialCitationCount}
summary: {p.tldr}
pdf: {p.openAccessPdf}"""
    
    async def _arun(self, query: str, run_manager = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
 
class SemanticScholarToolkit(BaseToolkit):
    def get_tools(self):
        return [SemanticScholarSearch(), SemanticScholarRead()]



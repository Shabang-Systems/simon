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
    
class SemanticScholarGet(BaseTool):
    name = "semantic_paper_get"
    description = "Uses the paperId as action input to get information about a paper. Provide nothing except for the exact paper ID. For instance, if the paper's ID is d696b35956e38351dd2eae67068aecff8d381cfe, provide literally `d696b35956e38351dd2eae67068aecff8d381cfe` If the paper's link is https://arxiv.org/abs/1706.03762, provide literally `1706.03762`. Do not add quotations, do not add special symbols like `. Do not include the word paperId."

    def _run(self, query: str, run_manager = None) -> str:
        engine = SemanticScholar()
        # get only the paperid part
        query = query.split(":")[-1].strip()
        query = query.split("(")[0].strip()
        query = query.split("=")[-1].strip()
        query = query.replace("`", "")
        # get paper ID
        try: 
            if "/" in query:
                # DOI
                p = SCHOLAR.get_paper(f"DOI:{query}")
            elif "." in query:
                # arxiv id
                p = SCHOLAR.get_paper(f"ARXIV:{query}")
            else:
                # normal
                p = SCHOLAR.get_paper(query)
            # if pdf, get pdf
            pdf = p.openAccessPdf
            # if pdf
            if pdf:
                pdf = pdf["url"]
            # otherwise, if arxiv, extract that
            if not pdf and p.venue == "arXiv.org":
                pdf = f'https://arxiv.org/pdf/{p["externalIds"]["ArXiv"]}'
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
pdf: {pdf}"""
    
    async def _arun(self, query: str, run_manager = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
 
class SemanticScholarToolkit(BaseToolkit):
    def get_tools(self):
        return [SemanticScholarSearch(), SemanticScholarGet()]



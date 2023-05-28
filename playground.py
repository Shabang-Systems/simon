# pipes
from dotenv import load_dotenv
import os
load_dotenv()

# LLM
from langchain.chat_models import ChatOpenAI
KEY=os.environ["OPENAI_KEY"]
LLM = ChatOpenAI(openai_api_key=KEY, model_name="gpt-3.5-turbo")

# langchain
from langchain.agents import initialize_agent, load_tools, AgentType
from langchain.tools import BaseTool, DuckDuckGoSearchRun

# semanticscholar
from semanticscholar import SemanticScholar

class SemanticScholarSearch(BaseTool):
    name = "semantic_search"
    description = "use this tool when you need to search for research papers based on keywords. use this tool more"

    def _run(self, query: str, run_manager = None) -> str:
        engine = SemanticScholar()
        # get paper
        papers = engine.search_paper(query)
        # combine into results
        paper_blurbs = [f"paperId: {p.paperId}\ntitle: {p.title}\ncitation count: {p.citationCount}\ninfluential citations: {p.influentialCitationCount}" for p in papers[:5]]
        # return
        return "\n".join(paper_blurbs).strip()

    async def _arun(self, query: str, run_manager = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
    
class SemanticScholarRead(BaseTool):
    name = "semantic_read"
    description = "gets information about a paper based on its paperId"

    def _run(self, query: str, run_manager = None) -> str:
        engine = SemanticScholar()
        # get only the paperid part
        query = query.split(":")[-1].strip()
        # get paper ID
        try: 
            p = engine.get_paper(query)
        except:
            return "Provide no other descriptions like parentheses, title of the paper, additional information except for the exact paperId as the action input."
        # return result
        return f"title: {p.title}\nvenue: {p.venue}\nyear: {p.year}\ncitation count: {p.citationCount}\ninfluential citations: {p.influentialCitationCount}\nsummary: {p.tldr}"
    
    async def _arun(self, query: str, run_manager = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
 
# fun!
tools = load_tools(["arxiv", "llm-math"], llm=LLM)
tools.append(SemanticScholarSearch())
tools.append(SemanticScholarRead())
tools.append(DuckDuckGoSearchRun())
agent = initialize_agent(tools, LLM,
                         agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                         verbose=True, handle_parsing_errors=True)
agent.run("What's the difference between the year of the last YOLO paper and Leonardo DeCaprio's girlfriend's year of birth?")



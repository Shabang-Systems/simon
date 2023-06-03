# langchain stuff
from langchain.tools import Tool
from langchain.agents import ZeroShotAgent, AgentExecutor

# context
from ..models import AgentContext

# tools
from ..toolkits import SemanticScholarToolkit, DocumentProcessingToolkit

def CatalogAgent(context:AgentContext):
    # we only care about the last tool (read a single document) for the research agent
    tools = DocumentProcessingToolkit(context.elastic, context.embedding, context.uid).get_tools()
    agent = ZeroShotAgent.from_llm_and_tools(llm=context.llm, tools=tools)

    return agent, tools

def Catalog(context:AgentContext, verbose=False):
    agent, tools = CatalogAgent(context)
    executor = AgentExecutor.from_agent_and_tools(agent, tools, verbose=verbose, handle_parsing_errors=True)

    tool = Tool.from_function(func=lambda x:executor.run(x),
                              name = "document-catalog",
                              description="Useful when you need to answer questions using prior knowledge using documents you have seen before, including papers, emails, articles, websites, etc. Provide with tool with a natural language statement or question, and it will return a natural language answer. Do not use this tool if you are looking for new information. This tool can only tell you information using facts gathered from the documents.")

    return tool


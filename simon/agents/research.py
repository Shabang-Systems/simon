# langchain stuff
from langchain.tools import Tool
from langchain.agents import ZeroShotAgent, AgentExecutor

# context
from ..models import AgentContext

# tools
from ..toolkits import SemanticScholarToolkit, DocumentProcessingToolkit

def ResearchAgent(context:AgentContext):
    # we only care about the last tool (read a single document) for the research agent
    tools = SemanticScholarToolkit().get_tools() + DocumentProcessingToolkit(context.elastic,
                                                                             context.embedding,
                                                                             context.uid).get_tools()[-1:]
    agent = ZeroShotAgent.from_llm_and_tools(llm=context.llm, tools=tools)

    return agent, tools

def Research(context:AgentContext, verbose=False):
    agent, tools = ResearchAgent(context)
    executor = AgentExecutor.from_agent_and_tools(agent, tools, verbose=verbose, handle_parsing_errors=True)

    tool = Tool.from_function(func=lambda x:executor.run(x),
                              name = "scientific-articles",
                              description="Useful when you need to answer questions about academic papers and scientific studies. Provide a natural language question, and the tool will return a natural language response. Do not use this tool to answer questions that would require information about the user's interaction with the tool, as it retains no prior information. Only use this tool if you are looking up new, objective scientific facts.")

    return tool


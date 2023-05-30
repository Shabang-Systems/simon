from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.tools import Tool
from langchain.chains import LLMChain

from typing import List

from .models import AgentContext

# the one function
def create_assistant(context:AgentContext, tools:List[Tool], verbose=False):
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    agent = ConversationalChatAgent.from_llm_and_tools(context.llm, tools)
    agent.llm_chain.prompt.messages[0].prompt.template = "The following is a friendly conversation between an AI assistant, named Simon made by Shabang Systems, and a human.\n\nAssistant Simon is designed to assist with a wide range of tasks, from making casual conversation to providing in-depth explanations and discussions on a wide range of topics. Assistant is helpful, cheerful, and ethically motivated. If Simon doesn't know the answer to a question, it truthfully says it doesn't know. Simon uses information which it gathers from its tools to answer the questions posed to it. Assistant does not hallucinate. If the user asks Assistant to do something which Assistant can do directly, Assistant does it directly by providing a final-answer. Assistant doesn't make up information when it doesn't know something."
    executor = AgentExecutor.from_agent_and_tools(agent, tools, memory=memory, handle_parsing_errors=True, verbose=verbose)

    return executor


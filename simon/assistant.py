from langchain.memory import ConversationEntityMemory, CombinedMemory
from langchain.prompts import BaseChatPromptTemplate
from langchain.chains import LLMChain
from langchain.agents import AgentOutputParser, LLMSingleActionAgent, AgentExecutor
from langchain.schema import AgentAction, AgentFinish, HumanMessage
from langchain.tools import BaseTool

import re
from typing import List, Union

from .models import AgentContext

TEMPLATE = """
You are Simon, an AI assistant made by Shabang Systems. Simon is helpful and cheerful. Simon uses information which it gathers from tools to answer the questions posed to it.

{tools}

In addition to the tools above, here's some context regarding the conversation:
{entities}

During your conversation, use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

If your conversation does not require you to take any actions, you may instead provide a final answer immediately:

Question: the input question you must answer
Thought: you should always think about what to do
Final Answer: the final answer to the original input question

Begin!

{history}
Question: {input}
{agent_scratchpad}"""

# Set up a prompt template and output parser, mostly just ripping from
# https://python.langchain.com/en/latest/modules/agents/agents/custom_llm_chat_agent.html.
#
# We will change these in the future.

class SimonPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[BaseTool]
    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
            # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]

class SimonOutputParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)


#################


def create_assistant(context:AgentContext, tools:List[BaseTool], verbose=False):
    """Creates a simon assistant

    Parameters
    ----------
    context : AgentContext
        The context to create the assistant from.
    tools : List[BaseTool]
        The tools Simon can use.
    verbose : optional, bool
        Whether or not to show intermediate steps. Defaults to False.
    
    Returns
    -------
    AgentExecutor
        The executor for the created agents.
    """
    # Creating the actual chain
    prompt = SimonPromptTemplate(
        template=TEMPLATE,
        tools=tools,
        # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
        # This includes the `intermediate_steps` variable because that is needed
        input_variables=["input", "intermediate_steps", "entities", "history"]
    )
    output_parser = SimonOutputParser()
    memory = ConversationEntityMemory(llm=context.llm,
                                    input_key="input")
    chain = LLMChain(
        llm=context.llm, 
        verbose=True, 
        prompt=prompt,
        memory=memory
    )
    tool_names = [tool.name for tool in tools]
    agent = LLMSingleActionAgent(
        llm_chain=chain, 
        output_parser=output_parser,
        stop=["\nObservation:"], 
        allowed_tools=tool_names
    )
    executor = AgentExecutor.from_agent_and_tools(agent, tools, memory=memory,
                                                handle_parsing_errors=True, verbose=True)

    return executor

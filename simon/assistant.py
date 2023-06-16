from langchain.memory import ConversationEntityMemory, CombinedMemory
from langchain.prompts import BaseChatPromptTemplate
from langchain.chains import LLMChain
from langchain.agents import AgentOutputParser, LLMSingleActionAgent, AgentExecutor
from langchain.schema import AgentAction, AgentFinish, HumanMessage, OutputParserException
from langchain.tools import BaseTool, Tool

import re
from typing import List, Union
from datetime import datetime

from .models import AgentContext
from .utils.elastic import kv_set, kv_getall

TEMPLATE = """
You are Simon, an assistant made by Shabang Systems. Simon uses information which it gathers from tools to answer the questions posed to it. 

To help answer questions from the user, you have access from to the following tools:

{tools}
finish: finish is ALWAYS the final action you should perform. This tool provides the input you provide back to the human. The input to this tool should be the answer to the human's question.

During your conversation, use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}, finish]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Action: finish
Action Input: the full, contexualized answer to the initial question provided by the user

Remember, a "Thought:" line must be followed by an "Action:" line AND "Action Input: " line. Only provide ONE Action: finish line in your output. Never provide multiple as it will not be presented to the user.

For your reference, here are the past conversations between you and the human:

{history}

Here are some infromation that maybe helpful to you to answer the user's questions:

{entities}

If you can answer the user's question just inferring from the information above, do not use other tools.

Lastly, today's date is {date}. It is currently {time}. {human_intro}

Begin!

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
    # human intro
    human_intro: str = ""
    
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # pop out the entities, and append
        entities = kwargs.pop("entities")

        kwargs["date"] = datetime.now().strftime("%A, %B %d, %Y")
        kwargs["time"] = datetime.now().strftime("%H:%M:%S")

        if self.human_intro != "":
            kwargs["human_intro"] = "Here's an introduction from the human working with you: "+self.human_intro

        kwargs["entities"] = "\n".join([f"{key}: {value}" for key, value in entities.items()]).strip()
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        # we index until -1 because the last tool is the failsafe identity tool
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        # we index until -1 because the last tool is the failsafe identity tool
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]

class SimonOutputParser(AgentOutputParser):
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Action: finish" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Action Input:")[-1].strip()},
                log=llm_output
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Action Input:")[-1].strip()},
                log=llm_output
            )
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

#################


class Assistant:

    def __init__(self, context:AgentContext, tools:List[BaseTool], human_intro:str="", verbose=False):
        """Creates a simon assistant

        Parameters
        ----------
        context : AgentContext
            The context to create the assistant from.
        tools : List[BaseTool]
            The tools Simon can use.
        human_intro : optional, str
            An introduction from the human.
        verbose : optional, bool
            Whether or not to show intermediate steps. Defaults to False.

        Returns
        -------
        AgentExecutor
            The executor for the created agents.
        """


        # create the entity memory
        memory = ConversationEntityMemory(llm=context.llm,
                                          input_key="input")
        # memory_tool = Tool.from_function(func = lambda q: "\n".join([f"{key}: {value}"
        #                                                              for key, value
        #                                                              in memory.load_memory_variables({"input":q.strip("\"").strip()})["entities"].items()]),
        #                                  name="entity_retrieval",
        #                                  description="Retrieve information about an entity (person, location, etc.) that may have came up in conversations with the user. This tool only has information about a few entities. Provide this tool the name of the entity you want information about.")
        
        human_tool = Tool.from_function(func = lambda q: input(f" ").strip(),
                                        name="human",
                                        description="You can ask a human a follow up question using this tool when you are stuck. Do NOT ask factual questions. Supply a question you would ask a human to this tool. The input to your tool should begin with \"I didn't understand your question; can you clarify what you meant when you said\"")

        tools_packaged = tools + [human_tool]
        # Creating the actual chain
        prompt = SimonPromptTemplate(
            template=TEMPLATE,
            tools=tools_packaged,
            human_intro=human_intro,
            # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
            # This includes the `intermediate_steps` variable because that is needed
            input_variables=["input", "intermediate_steps", "entities", "history"]
        )
        output_parser = SimonOutputParser()
        kv = kv_getall(context.elastic, context.uid)
        memory.entity_store.store = kv
        chain = LLMChain(
            llm=context.llm, 
            verbose=True, 
            prompt=prompt,
            memory=memory
        )
        tool_names = [tool.name for tool in tools_packaged]
        agent = LLMSingleActionAgent(
            llm_chain=chain, 
            output_parser=output_parser,
            stop=["\nObservation:"], 
            allowed_tools=tool_names
        )
        self.__executor = AgentExecutor.from_agent_and_tools(agent, tools_packaged, memory=memory,
                                                             handle_parsing_errors=True, verbose=verbose)
        self.__context = context

    def __call__(self, query):
        result = self.__executor(query)
        kv = self.knowledge

        # store memory context key value in elastic
        for key,value in kv.items():
            kv_set(key, value, self.__context.elastic, self.__context.uid)

        return result.get("output", "")

    @property
    def knowledge(self):
        return self.__executor.memory.entity_store.store
        


        

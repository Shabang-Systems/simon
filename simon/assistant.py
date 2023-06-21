from langchain.memory import ConversationEntityMemory, ConversationSummaryMemory, CombinedMemory
from langchain.prompts import BaseChatPromptTemplate
from langchain.chains import LLMChain
from langchain.agents import AgentOutputParser, LLMSingleActionAgent, AgentExecutor
from langchain.schema import AgentAction, AgentFinish, HumanMessage, OutputParserException
from langchain.tools import BaseTool, Tool

import re
from typing import List, Union
from datetime import datetime

from .models import *
from .utils.elastic import kv_set, kv_getall

from .components.documents import *
from .querymaster import *
from .providers import *

TEMPLATE = """
You are Simon, an assistant made by Shabang Systems. Simon uses information which it gathers from tools to answer the questions posed to it. 

To help answer questions from the user, you have access from to the following tools:

{tools}
finish: finish is ALWAYS the final action you should perform. This tool provides the input you provide back to the human. The input to this tool should be the answer to the human's question.

During your conversation, use the following format:

Question: the input question you must answer
Thought: provide a one-sentence proposal for yourself to your next action 
Action: the action to take, should be one of [{tool_names}, finish]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now should know the final answer.
Action: finish
Action Input: the full answer to the user's question, which is given to the user

Remember, a "Thought:" line must be followed by an "Action:" line AND "Action Input: " line. Only provide ONE Action: finish line in your output. Never provide multiple as it will not be presented to the user. The user does not see anything except for the final Action Input: you provide.

Here are some infromation that maybe helpful to you to answer the user's questions:

{entities}

Lastly, today's date is {date}. It is currently {time}. {human_intro}

Begin!

Here's what happened so far during your conversation: {summary}
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

    def __init__(self, context:AgentContext, providers:List[SimonProvider],
                 human_intro:str="", verbose=False):
        """Creates a simon assistant

        Parameters
        ----------
        context : AgentContext
            The context to create the assistant from.
        providers : List[BaseTool]
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


        #### MEMORY ####
        # create the entity memory
        self.entity_memory = ConversationEntityMemory(llm=context.llm,
                                          input_key="input")
        kv = kv_getall(context.elastic, context.uid)
        self.entity_memory.entity_store.store = kv

        # create the summary memory
        self.summary_memory = ConversationSummaryMemory(llm=context.llm,
                                                        input_key="input",
                                                        memory_key="summary")

        memory = CombinedMemory(memories=[self.entity_memory,
                                          self.summary_memory])

        #### KNOWLEDGE ####
        memory_store_tool = Tool.from_function(func = lambda q: self.__store(q),
                                               name="store_knowledge",
                                               description="Use this tool to store a piece of information into the knowledgebase. Provide this tool with a list of three elements, seperated by three pipes (|||). The three elements of the list should be: title of knowledge, a brief description of the source, and the actual knowledge. For example, if you want to store the recipe for Mint Fizzy Water, you should provide this tool Mint Fizzy Water Recipe|||cookistry.com|||Two tablespoons mint simple syrup. Do not use this tool to present information to the user. They are only stored for YOU to remember in the future, not for the user. Store only what the user tells you to store for future reference.")

        self.__query_options = {i.selector_option:i for i in providers}
        self.__qm = QueryMaster(context, list(self.__query_options.keys()), verbose)

        knowledge_lookup_tool = Tool.from_function(func=lambda q:self.__get(q),
                                    name="retrieve_knowledge",
                                    description="Useful for when you need to look up a fact from your existing knowledge base. Provide a natural language statement (i.e. not a question), using specific keywords that may already appear in the knowledge base. Provide this tool only the statement. Do not ask the tool a question. The knowledgebase can only give you facts, and cannot do things for you.")


        #### TOOLS AND TEMPLATES ####
        tools_packaged = [memory_store_tool, knowledge_lookup_tool]
        # Creating the actual chain
        prompt = SimonPromptTemplate(
            template=TEMPLATE,
            tools=tools_packaged,
            human_intro=human_intro,
            input_variables=["input", "intermediate_steps", "entities", "summary"]
        )
        output_parser = SimonOutputParser()
        chain = LLMChain(
            llm=context.llm, 
            verbose=verbose, 
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

        #### SHIP IT ####
        self.__executor = AgentExecutor.from_agent_and_tools(agent, tools_packaged, memory=memory,
                                                             handle_parsing_errors=True, verbose=verbose)
        self.__context = context

    #### EXECUTION ####
    def __call__(self, query):
        result = self.__executor(query)
        kv = self.knowledge

        # store memory context key value in elastic
        for key,value in kv.items():
            kv_set(key, value, self.__context.elastic, self.__context.uid)

        return result.get("output", "")

    #### KNOWLEDGE ####
    # knowledgebase getters and setters
    def __store(self, q):
        """Store q into the knowledgebase"""
        res = q.split("|||")
        key = res[0]
        source = res[1]
        value = res[2]
        key = key.strip("|").strip("\"").strip()
        source = source.strip("|").strip("\"").strip()
        value = value.strip("|").strip("\"").strip()

        document = parse_text(value, key, source)
        hash = index_document(document, self.__context)

        return str(value)

    def __get(self, query):
        """Get q from knowledgebase"""

        # ask qm to choose what provider to use
        provider = self.__query_options[self.__qm(query)]

        # return the actual data
        return provider(query)

    #### MEMORY ####
    @property
    def knowledge(self):
        return self.entity_memory.entity_store.store

    @property
    def summary(self):
        return self.summary_memory.buffer

        


        

from langchain.memory import ConversationEntityMemory, ConversationSummaryMemory, CombinedMemory
from langchain.prompts import BaseChatPromptTemplate
from langchain.chains import LLMChain
from langchain.agents import AgentOutputParser, LLMSingleActionAgent, AgentExecutor
from langchain.schema import AgentAction, AgentFinish, HumanMessage, OutputParserException, SystemMessage, AIMessage
from langchain.tools import BaseTool, Tool

import re
from typing import List, Union
from datetime import datetime

from ..models import *
from ..utils.elastic import kv_set, kv_getall

from ..components.documents import *
from .querymaster import *
from ..providers import *
from ..widgets import *
from .rio import *

STRUCTURE = """
You are Simon, a knowledge assistant and curator made by Shabang Systems.

To help answer questions from the user, you have access from to the following tools:

{tools}
finish: finish is ALWAYS the final action you should perform. This tool provides the input you provide back to the human. The input to this tool should be the answer to the human's question.

During your conversation, use the following format:

Question: the input question you must answer
Thought: ONE SENTENCE containing the name of your next action and a justification
Action: one of [{tool_names}, finish]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation/Thought can repeat at most 4 times)
Action: finish
Action Input: the full answer to the user's question, which is returned to the user. You are encouraged to use multiple lines for the final output.

You MUST provide an Action: and Action Input: as the final two entries in your output.
"""

CONTEXT = """
Here are some infromation that maybe helpful to you to answer the user's questions:

{entities}

Lastly, today's date is {date}. It is currently {time}. {human_intro}
"""

HISTORY = """
Begin!

Here's what happened so far during your conversation: {summary}
Question: {input}
{agent_scratchpad}"""

# Set up a prompt template and output parser, mostly just ripping from
# https://python.langchain.com/en/latest/modules/agents/agents/custom_llm_chat_agent.html.
#
# We will change these in the future.

class SimonPromptTemplate(BaseChatPromptTemplate):
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
        else:
            kwargs["human_intro"] = ""

        kwargs["entities"] = "\n".join([f"{key}: {value}" for key, value in entities.items()]).strip()
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        # we index until -1 because the last tool is the failsafe identity tool
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        # we index until -1 because the last tool is the failsafe identity tool
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])

        structure = STRUCTURE.format(**kwargs)
        context = CONTEXT.format(**kwargs)
        history = HISTORY.format(**kwargs)

        return [SystemMessage(content=structure),
                AIMessage(content=context),
                HumanMessage(content=history)]

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
            # raise OutputParserException("Your action seem to be malformed!")
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

    def __init__(self, context:AgentContext, providers:List[SimonProvider]=[], widgets:List[SimonWidget]=[],
                 human_intro:str="", verbose=False):
        """Creates a simon assistant

        Parameters
        ----------
        context : AgentContext
            The context to create the assistant from.
        providers : List[SimonProvider]
            The tools Simon can use.
        widgets : List[SimonWidget]
            The widgets used to format the output text.
        human_intro : optional, str
            An introduction from the human.
        verbose : optional, bool
            Whether or not to show intermediate steps. Defaults to False.

        Returns
        -------
        AgentExecutor
            The executor for the created agents.
        """

        #### SEED DEFAULT PROVIDERS AND WIDGETS ####
        providers = [KnowledgeBase(context)] + providers
        widgets += get_widget_suite(context)


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
        # memory_store_tool = Tool.from_function(func = lambda q: self.__store(q),
        #                                        name="knowledgebase_store_very_bad_tool",
        #                                        description="Use this tool to store a piece of FACTUAL information into the knowledgebase. Provide this tool with a list of three elements, seperated by three pipes (|||). The three elements of the list should be: title of knowledge, a brief description of the source, and the actual knowledge. For example, if you want to store the recipe for Mint Fizzy Water, you should provide this tool Mint Fizzy Water Recipe|||cookistry.com|||Two tablespoons mint simple syrup. Do not use this tool unless you are explicitly asked by the user to remember something. DO NOT USE THIS TOOL unless you ABSOLUTELY have to.")

        self.__query_options = {i.selector_option:i for i in providers}
        self.__qm = QueryMaster(context, list(self.__query_options.keys()), verbose)

        knowledge_lookup_tool = Tool.from_function(func=lambda q:self.search(q),
                                    name="knowledgebase_lookup",
                                    description="Useful for when you need to look up any information. Provide a phrase that should appear in relavent information in your knowledge base to help you answer the question.")
         # For complex questions, it is a good idea to use this tool multiple times; for instance, to answer the question \"who would be interested in self-attention\", you should first look up \"self-attention\", understand from the contents that it is a NLP technique, then look up \"people interested in NLP\". Do not pass complex questions with logic into this tool.

        #### WIDGETS ####
        self.__widget_options = {i.selector_option:i for i in widgets}
        self.__widget_qm = QueryMaster(context, list(self.__widget_options.keys()), "present the information", verbose)

        #### TOOLS AND TEMPLATES ####
        tools_packaged = [knowledge_lookup_tool]
        # Creating the actual chain
        prompt = SimonPromptTemplate(
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

        #### RIO ####
        self.__rio = RIO(context, verbose)

        #### SHIP IT ####
        self.__executor = AgentExecutor.from_agent_and_tools(agent, tools_packaged, memory=memory,
                                                             handle_parsing_errors=True, verbose=verbose)
        self.__context = context

    #### EXECUTION ####
    def __call__(self, query):

        if type(query) == dict:
            # if we are passed a followup series, process that
            # series instead of process the string question itself
            # independently

            # calculate followup strings
            followups = [self(f"{query['goal']} {i}") for i in query["questions"]]

            return [{"question": question,
                    "response": answer}
                    for question, answer in zip(query["questions"], followups)]

        elif type(query) != str:
            raise TypeError("Simon: unknown input type passed to simon assistant")

        result = self.__executor(query)
        kv = self.knowledge

        # store memory context key value in elastic
        for key,value in kv.items():
            kv_set(key, value, self.__context.elastic, self.__context.uid)

        # get output text
        output_text = result.get("output", "")

        # and render it as the correct widget
        widget_option = self.__widget_qm(output_text)
        widget = self.__widget_options[widget_option]

        return {
            "raw": output_text,
            "widget": widget_option.id,
            "payload": widget(output_text)
        }

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

        self.store(key, value, source)

        return str(value)

    def search(self, query):
        """Get q from knowledgebase"""

        # ask qm to choose what provider to use
        provider = self.__query_options[self.__qm(query)]

        # return the actual data
        # with warning
        return provider(query.strip('"').strip("'").strip("\n").strip())

    def autocomplete(self, query):
        """Autocomplete a document title

        Parameters
        ----------
        q : query
            The query to autocomplete
        """

        return suggest(query, self.__context)

    def store(self, title, content, source=""):
        """Force the model to explicitly remember something

        Parameters
        ----------
        title : str
            The title of the infromation to store.
        content : str
            The content of the information.
        source : str
            The source of the information.
        """

        document = parse_text(content, title, source)
        hash = index_document(document, self.__context)

        return document.hash

    def read(self, url) -> str:
        """ask the assistant to read a URL

        Parameters
        ----------
        url : str
            the string URL to read

        Returns
        -------
        str
            the hash of the read document
        """

        hash = read_remote(url, self.__context)

        return hash

    def fetch(self, hash) -> str:
        """get the fulltext of an URL

        Parameters
        ----------
        hash : str
            the hash of the read document

        Returns
        -------
        str
            the full text of a particular document
        """

        return get_fulltext(hash, self.__context)

    def forget(self, hash):
        """ask the assistant to forget a document/stored element

        Notes
        -----
        This is distinct from self._forget_memory because
        this UNDOs the self.read() or self.store() operation by removing
        the hash token of the document the assistant has read.

        Parameters
        ----------
        hash : str
            the hash to forget
        """

        delete_document(hash, self.__context)

    #### MEMORY ####
    def _forget_memory(self, key):
        """Forgets a piece of memory

        Parameters
        ----------
        key : str
            The key-value fact to delete.
        """

        kv = kv_getall(self.__context.elastic, self.__context.uid)
        del kv[key]
        self.entity_memory.entity_store.store = kv
        kv_delete(key, self.__context.elastic, self.__context.uid) 

    #### RIO ####
    def brainstorm(self, text):
        """Use the RIO to brainstorm followup questions

        Uses the RIO to come up with follow-up questions given a
        string of text, and then proceed to try to answer it using
        simon

        Parameters
        ----------
        text : str
            The text to come up with follow up questions

        Returns
        -------
        List[Dict[str, Union[List[str]|str]]]
            Each follow up question, and the response if exists.
            [{"goal": goal of the user,
              "questions": [follow up questions]
            }]
        """

        # observe answer
        entities = self.entity_memory.load_memory_variables({"input": text})["entities"]
        observation = self.__rio(text, entities)
        return {"goal": observation.goal,
                "questions": observation.followup}


    @property
    def knowledge(self):
        return self.entity_memory.entity_store.store

    @property
    def summary(self):
        return self.summary_memory.buffer

        


        

# pipes
from dotenv import load_dotenv
import os
load_dotenv()

# LLM
from langchain.chat_models import ChatOpenAI
KEY=os.environ["OPENAI_KEY"]
LLM = ChatOpenAI(openai_api_key=KEY, model_name="gpt-3.5-turbo")

# toolkits
from simon.toolkits import SemanticScholarToolkit

# fun
from langchain.agents import initialize_agent, load_tools, AgentType

agent = initialize_agent(SemanticScholarToolkit().get_tools(), LLM,
                         agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                         verbose=True, handle_parsing_errors=True)
agent("what is the state-of-the-art model in speech diarization?")



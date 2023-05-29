# pipes
from dotenv import load_dotenv
import os
load_dotenv()

KEY=os.environ["OPENAI_KEY"]
ELASTIC_URL=os.environ["ELASTIC_URL"]
ELASTIC_USER=os.environ["ELASTIC_USER"]
ELASTIC_PASSWORD=os.environ["ELASTIC_PASSWORD"]

# LLM
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

# DB
from elasticsearch import Elasticsearch

# our toolkits
from simon.agents import Research
from simon.models import *

from simon.assistant import create_assistant

# fun
from langchain.agents import AgentExecutor

# llms
llm = ChatOpenAI(openai_api_key=KEY, model_name="gpt-3.5-turbo")
embedding = OpenAIEmbeddings(openai_api_key=KEY, model="text-embedding-ada-002")

# db
es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
UID = "test-uid"

context = AgentContext(llm, embedding, es, UID)


tool = Research(context, True)

assistant = create_assistant(context, [tool])
assistant.run("Hey Simon you are doing waayy too much.")
# assistant

# AgentExecutor.from_agent_and_tools(agent, t, verbose=True, handle_parsing_errors=True)("What's so good about the state-of-the-art speech diarization model?")

# 

# fun!
# tools = SemanticScholarToolkit().get_tools() + DocumentProcessingToolkit(es, embedding, UID).get_tools()
# agent = initialize_agent(tools, llm,
#                          agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#                          verbose=True, handle_parsing_errors=True)

# agent()

# # import
# from simon.agents.research import 


# # from simon.toolkits.documents import *
# # hash = index_remote_file("https://arxiv.org/pdf/2105.13802.pdf", es, embedding, UID)
# # res = nl_search("what's the abstract of this paper?", es, embedding, UID, hash)
# # res1 = bm25_search("what's the abstract of this paper?", es, embedding, UID, hash)

# # # tmp = embedding.embed_documents(["this is a test", "I am a test indeed"])
# # # len(tmp[1])



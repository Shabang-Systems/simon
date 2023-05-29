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
from simon.toolkits import SemanticScholarToolkit, DocumentProcessingToolkit

# fun
from langchain.agents import initialize_agent, load_tools, AgentType

# llms
llm = ChatOpenAI(openai_api_key=KEY, model_name="gpt-3.5-turbo")
embedding = OpenAIEmbeddings(openai_api_key=KEY, model="text-embedding-ada-002")

# db
es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
UID = "test-uid"


# fun!
tools = SemanticScholarToolkit().get_tools() + DocumentProcessingToolkit(es, embedding, UID).get_tools()
agent = initialize_agent(tools, llm,
                         agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                         verbose=True, handle_parsing_errors=True)
agent("What is different about the best speech diarization model right now compared to its predecessors?")


# from simon.toolkits.documents import *
# hash = index_remote_file("https://arxiv.org/pdf/2105.13802.pdf", es, embedding, UID)
# res = nl_search("what's the abstract of this paper?", es, embedding, UID, hash)
# res1 = bm25_search("what's the abstract of this paper?", es, embedding, UID, hash)

# # tmp = embedding.embed_documents(["this is a test", "I am a test indeed"])
# # len(tmp[1])



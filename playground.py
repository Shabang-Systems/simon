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

# serialize all of the above together
context = AgentContext(llm, embedding, es, UID)

# provision tools we need
tool = Research(context, True)

# and create the assistant.
assistant = create_assistant(context, [tool])
# assistant.run("Hey Simon.")

from simon.toolkits.documents import *
hash = index_remote_file("https://arxiv.org/pdf/1706.03762.pdf", context.elastic, context.embedding, context.uid)

es.search("simon-docs", query={})
doc = es.search(index="simon-fulltext", query={"bool": {"must": [{"match": {"hash": hash}},
                                                             {"match": {"user.keyword": context.uid}}]}},
                fields=["text"], size=10000)
hits = [i["fields"]["text"][0] for i in doc["hits"]["hits"]]
hits
text = "".join(hits)
es.indices.delete(index="simon-cache")
es.indices.delete(index="simon-docs")

from simon.toolkits.documents import _seed_schema
_seed_schema(es)




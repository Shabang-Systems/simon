# pipes
from dotenv import load_dotenv
import os
load_dotenv()

KEY=os.environ["OPENAI_KEY"]
ELASTIC_URL=os.environ["ELASTIC_URL"]
ELASTIC_USER=os.environ["ELASTIC_USER"]
ELASTIC_PASSWORD=os.environ["ELASTIC_PASSWORD"]

# LLM
from langchain.agents import load_tools
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

# DB
from elasticsearch import Elasticsearch

# our toolkits
from simon.agents import Research, Catalog
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
research = Research(context, True)
catalog = Catalog(context, True)
human = load_tools(["human"])[0]

# and create the assistant,.
# , catalog

from simon.toolkits.documents import *

index_remote_file

index_remote_file("https://www.mdpi.coaoenustahom/1996-1944/15/18/6283/pdf?version=1663048430", es, embedding, UID)

assistant = create_assistant(context, [research, human], True)
assistant.run("Can you try a little harder? What is mycelium in the first place?")
# assistant.run("Sure. Mason's ")
# assistant.run("Without using tools, can you write an email about the topic?")
# assistant.run("Can you summarize what we did together today?")
# assistant.run("Have Simon ever read a document written by Vaswani?")


# # from simon.toolkits.documents import *


# # key="key"
# # value="value"
# # uid=UID
# # user = uid

# # es.index(index="simon-kv", document={"key":key,
# #                                      "value":value,
# #                                      "user": uid})
    
# # hash = index_remote_file("https://cdn.icyflamestudio.com/wp-content/uploads/download-test-file.jpg", context.elastic, context.embedding, context.uid)
# # hash
# # doc = read(hash, context.elastic, context.uid)
# # doc

# # es.search("simon-docs", query={})
# # text = "".join(hits)
# # es.indices.delete(index="simon-cache")
# # es.indices.delete(index="simon-docs")

# # from simon.toolkits.documents import _seed_schema
# # _seed_schema(es)




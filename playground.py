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
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.tools import DuckDuckGoSearchRun

# DB
from elasticsearch import Elasticsearch

# our toolkits
from simon.models import *
from simon.components.documents import *
from simon.toolkits import KnowledgebaseToolkit

from simon.assistant import Assistant

# fun
from langchain.agents import AgentExecutor

# llms
llm = ChatOpenAI(openai_api_key=KEY, model_name="gpt-3.5-turbo-0613", temperature=1)
# llm = OpenAI(openai_api_key=KEY, model_name="text-davinci-003")
embedding = OpenAIEmbeddings(openai_api_key=KEY, model="text-embedding-ada-002")

# db
es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
UID = "test-uid"
# UID = "test-uid-alt"

# # serialize all of the above together
context = AgentContext(llm, embedding, es, UID)

# provision tools we need
tools = KnowledgebaseToolkit(context).tools

# create assistant
assistant = Assistant(context, tools, True)

# get_hash("https://machinelearning.apple.com/research/panoptic-segmentation", context)
# delete_document("6108645a3b902739691b6a6cfed328844f7a263f6de55ed2668385d28377f9b6", context)

# Can you write an email asking for my friend Kian's schedule next Tuesday? I want to have lunch with him.
# Great. Can you pop in some recommendations to Mediterranean places in Mountain View 

# assistant.knowledge


# from langchain.memory import ConversationKGMemory
# memory = ConversationKGMemory(llm=context.llm)
# memory.save_context({"input": "say hi to sam"}, {"output": "who is sam"})
# memory.save_context({"input": "sam is a friend"}, {"output": "okay"})
# memory.load_memory_variables({"input": 'who is sam'})
# context.llm 



# assistant.knowledge

## REMINDER: assistant's kv loading is broken. instead of reading old ones
## it loads new ones still.


# "Thanks so much! Bob's email is bob@bob.com. Can you draft a funny email to him explaining what TalkBank is?"


# assistant.memory.entity_store.store

# research = Research(context, True)
# # catalog = Catalog(context, True)
# # internet = DuckDuckGoSearchRun()

# # # and create the assistant,.
# # # , catalog

# # from simon.toolkits.documents import *

# # index_remote_file

# # # index_remote_file("https://www.mdpi.coaoenustahom/1996-1944/15/18/6283/pdf?version=1663048430", es, embedding, UID)

# # print(assistant.run("What are the state-of-the-art speech diarization models?"))
# def nah(doc, context):
#     embedded = context.embedding.embed_documents(doc.paragraphs)
#     docs = [{"embedding": a,
#              "text": b}
#             for a,b in zip(embedded, doc.paragraphs)]
#     update_calls = [{"_op_type": "index",
#                      "_index": "simon-embeddings",
#                      "user": context.uid,
#                      "metadata": doc.meta,
#                      "hash": doc.hash,
#                      "doc": i} for i in docs]
#     bulk(context.elastic, update_calls)


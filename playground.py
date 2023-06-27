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
from simon.providers import *

from simon.assistant import Assistant

# fun
from langchain.agents import AgentExecutor

# llms
llm = ChatOpenAI(openai_api_key=KEY, model_name="gpt-3.5-turbo-0613")
# llm = OpenAI(openai_api_key=KEY, model_name="text-davinci-003")
embedding = OpenAIEmbeddings(openai_api_key=KEY, model="text-embedding-ada-002")

# db
es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
UID = "test-uid"
# UID = "test-uid-alt"

# # serialize all of the above together
context = AgentContext(llm, embedding, es, UID)

# provision our data sources
kb = KnowledgeBase(context)
email = FakeEmail(context)

providers = [kb, email]

# create assistant
assistant = Assistant(context, providers,
                      "Hello! I am Jack, a first-year college student from the San Francisco Bay Area. My email is houjun@jemoka.com.", True)

# assistant.read("https://www.pnas.org/doi/full/10.1073/pnas.2006753117")

# print(kb("plastics depolymerization"))

# assistant.read("https://kaden.rice.edu/p2023-2.pdf")

# from simon.utils.elastic import *
# from simon.components.documents import *
# search("acmia corp", context)

# kv_delete("Batchalign", context.elastic, context.uid)

# search("batchalign 0.2.27 has been released", context)
# delete_document("bc83e0ed53a5705c6178a28c234d3853c84f73513df24741f4ba1e44822b6511", context)

# search("robert", context, search_type=IndexClass.KEYWORDS)
# assistant.store("Jacob", "Jacob is my friend working on IdeaFlow. He lives in Minnesota")
# assistant.store("Sam", "Sam is my friend doing some architecture in Ashland, Montana.")
# assistant.store("Acmia", "Acmia is an American company located in Minnesota.")

# from simon.components.documents import search, delete_document
# search("people in Minnesota", context)
# delete_document("75c3d630152611dcc71826ff5b3556db4427bbb7ae914590370f8432665e48a3", context)

# assistant._forget("Minnesota")

print(assistant("What are Rydberg atoms?"))

# print(kb("What is in Minnesota?"))

# assistant.knowledge["Minnesota"]
# print(assistant("What is Acmia?"))
# print(assistant("What does DementiaBank do? What are some interesting projects it works on?"))
# print(assistant("Can you summarize the contribution of RoseTTAFold2?"))
# print(assistant("Can you rewrite that summary and include a glossery of all the jargon?"))
# assistant.knowledge["Minnesota"]
# queries = [QuerySelectorOption("", "knowledgebase"),
#            QuerySelectorOption("Looks up the contents, addressees, and date and times of the emails sent by the user.", "email"),
#            QuerySelectorOption("Looks up the schedule of the user and their availability.", "schedule")]

# qm = QueryMaster(context, queries)
# qm("what is happening to Brian next week?")


# assistant.knowledge

# es
# _seed_schema(es)


# hash = read_remote("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7568301/", context)


# from simon.components.documents import *

# search("what is PETAse?", context)



# delete_document("e958bb20d131d87833c15183a722ef0732fa16d9e83e8e415702cbaef6e12ea4", context) 

# hash


# "Modify the email to ask for a meeting next Tuesday. Include full dates."
# assistant.summary
# assistant.knowledge

# get_hash("https://machinelearning.apple.com/research/panoptic-segmentation", context)



# delete_document("6108645a3b902739691b6a6cfed328844f7a263f6de55ed2668385d28377f9b6", context)

# print(assistant("Write an email in my tone to my boss Prof. MacWhinney, announcing batchalign 0.2.26, which fixed the issues with benchmarking. However, WER is still at 20%, which he can see with the attached .diff file. Tenses and contractions contribute the majority of the errors."))
# print(assistant("What are the differences between the installation instructions of batchalign vs. the re-installation instructions?"))
# read_remote("https://pypi.org/project/bpe/", context)

# 
# Great. Can you pop in some recommendations to Mediterranean places in Mountain View 


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


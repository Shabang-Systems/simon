# pipes
from dotenv import load_dotenv
import os
import json
load_dotenv()

KEY=os.environ["OPENAI_KEY"]
ELASTIC_URL=os.environ["ELASTIC_URL"]
ELASTIC_USER=os.environ["ELASTIC_USER"]
ELASTIC_PASSWORD=os.environ["ELASTIC_PASSWORD"]
MAPBOX_KEY=os.environ["MAPBOX_KEY"]

# LLM
from langchain.agents import load_tools
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.tools import DuckDuckGoSearchRun

from langchain.callbacks.manager import CallbackManager
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import LlamaCpp

# DB
from elasticsearch import Elasticsearch

# our toolkits
from simon import *

# fun
from langchain.agents import AgentExecutor

# llms
# llm = LlamaCpp(model_path="./opt/open_llama_7b/ggml-model-f16-q4_0.bin",
#                n_gpu_layers=1,
#                n_batch=128,
#                n_ctx=2048,
#                verbose=False)
llm = ChatOpenAI(openai_api_key=KEY, model_name="gpt-3.5-turbo-0613")
# llm = OpenAI(openai_api_key=KEY, model_name="text-davinci-003")
embedding = OpenAIEmbeddings(openai_api_key=KEY, model="text-embedding-ada-002")

# db
es = Elasticsearch(ELASTIC_URL, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
UID = "test-uid"
# UID = "test-uid-alt"

# # serialize all of the above together
context = AgentContext(llm, embedding, es, UID)

# provision our data sources (knowledgebase is provided by default)
map = Map(MAPBOX_KEY)
providers = [map]

# create assistant
assistant = Assistant(context, providers, verbose=True)
# assistant.read("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7568301/pdf/pnas.202006753.pdf") c3da811700fe0d4e5cc6f5a4e2d25410892fc3565657af6ab68d20f6bc0624a9
# assistant.forget("c3da811700fe0d4e5cc6f5a4e2d25410892fc3565657af6ab68d20f6bc0624a9")

# assistant._forget_memory("Robert")
# assistant._forget("Bay Area")
# thoughts = assistant.brainstorm("TODO: organize lunch with Robert")

# Robert dietary restrictions
# print(json.dumps(assistant(thoughts), sort_keys=True, indent=4))


# thoughts

#                  sort_keys=True, indent=4))

# assistant.brainstorm("")
# print(json.dumps(assistant(thoughts), sort_keys=True, indent=4))

# assistant("do you know if any good Chinese places I should go with Robert?")

# print(json.dumps(assistant(followup),
#                  sort_keys=True, indent=4))

# assistant.search("PETase")

# from simon.rio import *
# rio = RIO(context)
# rio("TODO: lunch with Robert next Tuesday")

# print(json.dumps(assistant("Can you give me more info about the restaurant Robert would like the best?"),
#                  sort_keys=True, indent=4))
# print(json.dumps(assistant("Which of my friends do you think I should talk about PETAse with?"),
#                  sort_keys=True, indent=4))

# print(json.dumps(assistant("I think the human is trying to schedule a lunch meeting with someone named Robert on a specific date and time. Where would the human like to have lunch?"),
#                  sort_keys=True, indent=4))

# print(assistant.search("user's friends"))
# assistant.

# from simon.components.documents import *
# search("companies to visit in Minnesota".lower(), context)

# print(kb("companies in Minnesota"))
# assistant.read("https://machinelearning.apple.com/research/panoptic-segmentation")
# from simon.components.documents import *

# delete_document('6108645a3b902739691b6a6cfed328844f7a263f6de55ed2668385d28377f9b6', context)

# from simon.utils.elastic import *
# from simon.components.documents import *
# search("acmia corp", context)

# kv_delete("Batchalign", context.elastic, context.uid)

# search("batchalign 0.2.27 has been released", context)
# delete_document("bc83e0ed53a5705c6178a28c234d3853c84f73513df24741f4ba1e44822b6511", context)

# search("robert", context, search_type=IndexClass.KEYWORDS)
# assistant.store("Jacob", "Jacob is my friend working on IdeaFlow. He lives in Minnesota") 0cabe870801b876cebbd8886d66e5c89c8622350f51cafcc29d234d6449014ab
# assistant.store("Batchalign update instructions", """
# Here are the instructions to update batchalign
# - conda activate batchalign
# - conda update batchalign -c jemoka -c conda-forge
# """) b5afefded670f4f6f2578999a8987f00236b651dd9f4198cec16a81fd383d4e6
# assistant.store("Robert", "Robert is a scientist working at Acmia's headquarters with a specialization in high-energy physics. He likes Chinese food a lot.") # 600165eb389d9da02ea160dcc1f8a0dc30b0a7a47588ae36c81e0189bcf98c02
# assistant.store("James", "James is a scientist working at Acmia's headquarters with research interest involving natural language processing.") bbcdde5962e2d63ee26093f61efc2d9d9bb99659bfc642dd771caa91810a5597
# assistant.store("Acmia", "Acmia is an American company located in Minnesota.") e459317fd1d86b0313e19d6f6a6c16c13c017cbef900bd650ca5b4f9ff6d96a3
# assistant.store("Sam", "Sam is my friend working as a painter in Flagstaff. She is very interested in sustainable plastics, especially new technologies to break down plastics.") #efd4f646158dc94fc85ba430b8efcf1190e9ee3388f7cc68098b0ac2102073e8
# assistant.store("Rupert", "Rubert lives in Minneapolis, but he's often in Saint Paul these days") e1743af286a07cd26b36843d10bfabf92bf5bfd8acd121747c9b1621be2c2afa
# from simon.components.documents import search, delete_document
# search("people in Minnesota", context)
# delete_document("75c3d630152611dcc71826ff5b3556db4427bbb7ae914590370f8432665e48a3", context)

# assistant._forget("Minnesota")

# assistant.read("https://kaden.rice.edu/p2023-2.pdf")
# print(assistant("Should I share this with any of my friends?"))
# print(assistant("Which of my friend should I share it with?"))
# print(assistant("Which of my friend should I share it with?"))
# print(assistant("Hmmmm. I wonder if I have a friend who may also be interested in this topic?"))

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


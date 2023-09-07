# Custom LLM/Connection
Basically every function in `simon` requires you to pass in a copy of an object named `AgentContext`. This structure describes your database and OpenAI credentials, and contains pointers to the language models running in the background which `simon` uses.

**Recommended: If you want to use `simon` using default settings, simply follow call `simon.create_context(...)` following the instructions in the [quick start guide](../start.md#connect-to-database).** The rest of this page is aimed at users wishing to customize which LLM is used, changing its parameters, changing the database connection type, etc.

## Customizing Context

If you want more control over the LLM or Database used, you can create a custom `AgentContext` object. You will need:

1. `langchain.llms.base.LLM` for grammar parsing and text manipulation LLM  (HellaSwag > 75 is good)
2. `langchain.llms.base.LLM` for high level reasoning (HellaSwag > 85 is good)
2. `langchain.embeddings.base.Embeddings` for chunk vector embedding; the vector dimension must be `1536`
3. `psycopg2.connection` as the database connection
4. `str` project name

For instance:

```python
# tools needed
from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from psycopg2 import connect

# simon
from simon import AgentContext

custom_context = AgentContext(
    ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key="sk-keyhere"),
    ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key="sk-keyhere"),
    OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key="sk-keyhere"),
    connect(**my_config),
    "project_name"
)

context = custom_context
```

And onwards and upwards with [ingest](../start.md#storing-some-files) or [search](../start.md#search-those-files) using your new `context`! You can use this method to swap out the models, the model parameters, the database connection, and anything else to your heart's content.

## Default Settings

By default, `simon` uses the following configuration to run its services:

- `llm`: `langchain.chat_models.ChatOpenAI gpt-3.5-turbo`, `temperature=0`
- `reason_llm`: `langchain.chat_models.ChatOpenAI gpt-4`, `temperature=0`
- `embedding`: `langchain.embeddings.OpenAIEmbeddings text-embedding-ada-002`, `temperature=0`
- `cnx`: `psycopg2.connection`


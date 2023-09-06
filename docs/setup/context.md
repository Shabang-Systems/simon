# Custom LLM/Connection
Basically every function in `simon` requires you to pass in a copy of an object named `AgentContext`. This structure describes your database and OpenAI credentials, and contains pointers to the language models running in the background which `simon` uses.

Here is the specification for this structure:

```python
@dataclass
class AgentContext:
    llm: langchain.llms.base.LLM # used for grammar parsing and text manipulation services
    reason_llm: langchain.llms.base.LLM # used for high level reasoning
    embedding: langchain.embeddings.base.Embeddings # used for chunk vector embedding
    cnx: Any # psql connection 
    uid: str # project ID

```

If you want to use `simon` using default settings, simply follow call `simon.create_context(...)` following the instructions in the [quick start guide](../start.md#connect-to-database). The rest of this page is aimed at users wishing to customize which LLM is used, changing the inference temperature, changing the database connection type, etc.

## Customizing Context

If you want more control over the LLM or Database used, you can create a custom `AgentContext` object.

## Default Settings

By default, `simon` uses the following configuration to run its services:

- `llm`: `langchain.chat_models.ChatOpenAI gpt-3.5-turbo`, `temperature=0`
- `reason_llm`: `langchain.chat_models.ChatOpenAI gpt-4`, `temperature=0`
- `embedding`: `langchain.embeddings.OpenAIEmbeddings text-embedding-ada-002`, `temperature=0`
- `cnx`: `psycopg2.connection`


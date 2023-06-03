
class DocumentProcessingToolkit():
    """A set of tools to process documents"""

    def __init__(self, elastic:Elasticsearch, embedding:Embeddings, user:str):
        self.es = elastic
        self.em = embedding
        self.uid = user

    def get_tools(self):
        keyword_lookup = Tool.from_function(func=lambda q:"\n".join(bm25_search(q, self.es, self.em, self.uid)),
                                    name="documents_keyword_search",
                                    description="Useful for when you need to lookup the user's knowledge base with keywords. Provide this tool only relavent keywords that would appear in the database.")

        lookup = Tool.from_function(func=lambda q:"\n".join(nl_search(q, self.es, self.em, self.uid)),
                                    name="documents_lookup_all",
                                    description="Useful for when you need to gather information to answer a question using every file ever seen by the user. Provide a properly-formed question to the tool. This tool doesn't return an answer; instead, it responds with some text that you can read to better help answer the question.")

        def lookup_file_f(q):
            try:
                read_remote = index_remote_file(q.replace("`", "").split(",")[0].strip(),
                                                self.es, self.em, self.uid)
            except ConnectionError:
                return "Hmmm... We don't seem to able to open this file. Can you try another one?"

            result = "\n".join(nl_search(q.replace("`", "").split(",")[1].strip(), self.es, self.em, self.uid,
                                         doc_hash=read_remote))
            return result

        lookup_file =  Tool.from_function(func=lookup_file_f,
                                    name="documents_lookup_file",
                                    description="Useful for when you need to gather information useful for answering a question using a file on the internet. The input to this tool should be a comma seperated list of length two; the first element of that list should be the URL of the file you want to read, and the second element of that list should be question. For instance, `https://arxiv.org/pdf/1706.03762,What is self attention?` would be the input if you wanted to look up the answer to the question of \"What is self attention\" from the PDF located in the link https://arxiv.org/pdf/1706.03762. Provide a properly-formed question to the tool. This tool doesn't return an answer; instead, it responds with some text that you can read to better help answer the question.")

        return [lookup, keyword_lookup, lookup_file]


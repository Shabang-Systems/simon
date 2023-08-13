import simon

import logging as L

DEBUG = True

LOG_FORMAT = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
L.basicConfig(format=LOG_FORMAT, level=L.WARNING)

if DEBUG:
    L.getLogger('simon').setLevel(L.DEBUG)


context = simon.create_context_oai("test-uid")
search = simon.Search(context)
store = simon.Datastore(context)

# print(store.store("https://neo.substack.com/p/neo-welcomes-suzanne-xie-as-investing"))
# print(search.query("Who is Suzanne?"))

# store.delete('c84597fc368a6dfd2f26ffe2581152740302005cdee878f80e6212c6e5260f8c')

# ing = JSONIngester(context)
# ing.ingest("https://www.jemoka.com/index.json", JSONMapping([StringMappingField("permalink", MappingTarget.SOURCE),
#                                                              StringMappingField("contents", MappingTarget.TEXT),
#                                                              StringMappingField("title", MappingTarget.TITLE)]))




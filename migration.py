import simon
context = simon.create_context("") 

# create stanging index
context.elastic.indices.create(index="simon-paragraphs-staging", mappings={"properties": {"hash": {"type": "keyword"},
                                                                                          "metadata.source": {"type": "text"},
                                                                                          "metadata.title": {"type": "completion"},
                                                                                          # paragraph number (seq / total)
                                                                         "metadata.seq": {"type": "unsigned_long"},
                                                                                          "metadata.tf": {"type": "float"},
                                                                                          "metadata.total": {"type": "unsigned_long"},
                                                                                          "text": {"type": "text"},
                                                                                          "embedding": {"type": "dense_vector",
                                                                                                        "dims": 1536,
                                                                                                        "similarity": "dot_product",
                                                                                                        "index": "true"},
                                                                                          "user": {"type": "keyword"}}})
# reindex the old data
from elasticsearch.helpers import reindex
reindex(context.elastic, "simon-paragraphs", "simon-paragraphs-staging")

# prevent writes on the staging index to prepare for cloning
context.elastic.indices.put_settings(settings={"index.blocks.write", "true"}, index="simon-paragraphs-staging")
# delete old index
context.elastic.indices.delete(index="simon-paragraphs")
# and clone to new index
context.elastic.indices.clone(index="simon-paragraphs-staging", target="simon-paragraphs")
# allow writes again
context.elastic.indices.put_settings(settings={"index.blocks.write", "false"}, index="simon-paragraphs-staging")


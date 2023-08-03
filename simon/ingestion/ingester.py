import logging
import os
import time

from elasticsearch import Elasticsearch

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

from simon import models
from simon.components import documents
from simon.environment import get_env_vars

from simon.ingestion import aws


def _build_agent_context(uid):
    logging.info('Setting up AgentContext...')

    env_vars = get_env_vars()
    logging.debug(f'Loaded environment variables: {env_vars}')

    openai_key = env_vars['OPENAI_KEY']
    llm = ChatOpenAI(
        openai_api_key=openai_key,
        model_name="gpt-3.5-turbo",
        temperature=0
    )
    embeddings = OpenAIEmbeddings(
        openai_api_key=openai_key,
        model="text-embedding-ada-002"
    )

    es_config = env_vars['ES_CONFIG']
    es = Elasticsearch(**es_config)

    context = models.AgentContext(
        llm=llm,
        reason_llm=llm,
        embedding=embeddings,
        elastic=es,
        uid=uid,
    )
    return context


class FileIngester:
    def __init__(self, agent_context=None, uid=None, source_prefix=None):
        if not agent_context and not uid:
            raise Exception(
                'Must provide either an AgentContext or a Simon UID to create AgentContext with.')
        if not agent_context:
            agent_context = _build_agent_context(uid)

        self.agent_context = agent_context
        self.source_prefix = source_prefix

    def _load_file(self, file_path):
        if aws.is_s3_uri(file_path):
            try:
                _, data = aws.read_file_from_s3(file_path)
                return data
            except Exception as e:
                logging.exception(
                    f'Erorr reading file {file_path} from S3: {e}')
                return None

        # Asusme local file if path not an S3 URI
        with open(file_path, 'r') as f:
            return f.read()

    def _make_source_str(self, file_path):
        if aws.is_s3_uri(file_path):
            # Ensure source always points to HTTPS form
            return aws.s3_uri_to_http(file_path)

        # Assume local file if path not an S3 URI
        file_name = os.path.basename(file_path)
        # This `source_prefix` setup is a bit hacky, but it works for now.
        # Basic idea is that it allows ingestion of local files that are uploaded somewhere else, and we want
        # the `source` for those documents to point to the canonical (remote) location.
        return self.source_prefix.rstrip('/') + '/' + file_name.lstrip('/')

    def ingest_file(self, file_path):
        title = os.path.basename(file_path)
        source = self._make_source_str(file_path)

        load_st = time.time()
        contents = self._load_file(file_path)
        load_et = time.time()
        if not contents:
            logging.error(f'Error loading {file_path}. Skipping...')
            return
        logging.info(
            f'Loaded {file_path} in {(load_et - load_st):.2f} seconds.')

        parse_st = time.time()
        document = documents.parse_text(contents, title=title, source=source)
        parse_et = time.time()
        logging.info(
            f'Parsed {title} in {(parse_et - parse_st):.2f} seconds.')

        indexed = False
        while not indexed:
            try:
                index_st = time.time()
                documents.index_document(document, context=self.agent_context)
                index_et = time.time()
                logging.info(
                    f'Indexed {title} in {(index_et - index_st):.2f} seconds.')
                indexed = True
            except:
                logging.exception(
                    f'Error indexing {title}. Retrying...')

    def ingest_all(self, files):
        ingest_all_st = time.time()
        for i, path in enumerate(files):
            file_name = os.path.basename(path)
            logging.info(
                f'Ingesting file {file_name} into ElasticSearch ({i} of {len(files)})...')
            self.ingest_file(path)
        ingest_all_et = time.time()
        logging.info('Ingestion done!')
        logging.info(
            f'Ingested {len(files)} files in {(ingest_all_et - ingest_all_st):.2f} seconds.')

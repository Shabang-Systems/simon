from ..components import documents, aws
from ..models import *
import time
import os
import logging
logging = logging.getLogger("simon")


class TextFileIngester:
    """Ingestor used for Local and S3 Text Files

    Parameters
    ----------
    context : AgentContext
        The context to ingest into
    source_prefix : str
    """

    def __init__(self, context: AgentContext, source_prefix=None):
        self.agent_context = context
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
        """Ingest a single file based on its URI.

        Parameters
        ----------
        file_path : str
            Single file paths (local or S3) to ingest.

        Returns
        -------
        str
            Hash of the ingested file, used for deletion later.
        """

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

        return document.hash

    def _parse_files_segment(self, files):
        parsed_docs = []
        for file_path in files:
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
            parsed = documents.parse_text(contents, title=title, source=source)
            parse_et = time.time()
            logging.info(
                f'Parsed {title} in {(parse_et - parse_st):.2f} seconds.')
            parsed_docs.append(parsed)
        return parsed_docs

    def ingest_all(self, files):
        """Ingest a group of files based on their URIs.

        Parameters
        ----------
        file_path : List[str]
            List of file paths (local or S3) to ingest.

        Returns
        -------
        List[str]
            Hashes of the ingested files, used for deletion later.
        """

        ingest_all_st = time.time()
        file_hashes = []
        segment_size = 50
        segments = [files[i:i+segment_size]
                    for i in range(0, len(files), segment_size)]
        logging.info(
            f'Split files list into {len(segments)} segments for ingestion.')
        for i, segment in enumerate(segments):
            logging.info(
                f'Ingesting sgment {i} of {len(segments)}...')
            seg_ingest_st = time.time()
            seg_parse_st = time.time()
            parsed = self._parse_files_segment(segment)
            seg_parse_et = time.time()
            logging.info(
                f'Parsed {len(segment)} files in {(seg_parse_et - seg_parse_st):.2f} seconds.')
            seg_index_st = time.time()
            documents.bulk_index(parsed, self.agent_context)
            seg_index_et = time.time()
            logging.info(
                f'Indexed {len(segment)} files in {(seg_index_et - seg_index_st):.2f} seconds.')
            seg_ingest_et = time.time()
            logging.info(
                f'Ingested {len(segment)} files in {(seg_ingest_et - seg_ingest_st):.2f} seconds.')

        ingest_all_et = time.time()
        logging.info('Ingestion done!')
        logging.info(
            f'Ingested {len(files)} files in {(ingest_all_et - ingest_all_st):.2f} seconds.')

        return file_hashes

import argparse
import logging
import multiprocessing
import os
import signal
import threading

from simon.components import aws
from simon.ingestion import TextFileIngester

def _setup_log_file(log_file):
    # Make intermediate directories if necessary
    if os.path.dirname(log_file):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    # Clear any previous log contents
    open(log_file, 'w').close()


def _configure_logger(debug=False, log_file=None):
    log_format = '[%(asctime)s] [%(name)s] [%(processName)s] [%(levelname)s] %(message)s'
    if debug:
        logging.basicConfig(format=log_format, level=logging.DEBUG)
    else:
        logging.basicConfig(format=log_format, level=logging.INFO)

    # Suppress chatty request logging from elasticsearch library
    logging.getLogger('elastic_transport.transport').setLevel(logging.WARNING)

    if log_file:
        _setup_log_file(log_file)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

    logging.info('Logger initialized.')


def _make_logger_thread(logger_queue):
    def thread_target():
        while True:
            record = logger_queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)

    return threading.Thread(target=thread_target)


def _find_files_to_ingest(file_paths):
    to_ingest = []
    for path in file_paths:
        if aws.is_s3_uri(path):
            logging.info(
                f'Finding all files at S3 URI {path} to be ingested...')
            s3_uris = aws.get_files_at_s3_uri(path)
            logging.debug(f'{len(s3_uris)} files found: {s3_uris}')
            to_ingest.extend(s3_uris)
        elif os.path.isdir(path):
            logging.info(
                f'Finding all files in directory {path} to be ingested...')
            dir_files = []
            for root, _, files in os.walk(path):
                for file in files:
                    dir_files.append(os.path.join(root, file))
            logging.debug(f'{len(dir_files)} files found: {dir_files}')
            to_ingest.extend(dir_files)
        else:
            to_ingest.append(path)

    logging.info(f'{len(to_ingest)} files found for ingestion.')
    return to_ingest


def _configure_worker_logger(logger_queue=None, debug=False):
    if not logger_queue:
        raise Exception(
            'Must provide a Queue to route worker logs through.')

    # Clear any inherited log handlers so all logging will go through queue
    logging.getLogger().handlers.clear()

    from logging.handlers import QueueHandler
    log_handler = QueueHandler(logger_queue)
    logging.getLogger().addHandler(log_handler)

    log_level = logging.DEBUG if debug else logging.INFO
    logging.getLogger().setLevel(log_level)

    # Suppress chatty request logging from elasticsearch library
    logging.getLogger('elastic_transport.transport').setLevel(logging.WARNING)

    logging.info('Worker logger initialized.')


def _make_ingestion_worker(files=[], ingester_args={}, logger_args={}):
    def process_target():
        _configure_worker_logger(**logger_args)
        ingester = TextFileIngester(**ingester_args)
        ingester.ingest_all(files)

    return multiprocessing.Process(target=process_target)


# Handle keyboard interrupts (ctrl+C from console); without this, workers will not be terminated
def _handle_keyboard_interrupt(*args):
    # Get the current process ID
    current_process_id = os.getpid()

    # Terminate all child processes
    for process in multiprocessing.active_children():
        if process.pid != current_process_id:
            process.terminate()

    # Exit the main process (if needed)
    raise SystemExit(f"KeyboardInterrupt (PID: {current_process_id})")


signal.signal(signal.SIGINT, _handle_keyboard_interrupt)


def main(args):
    _configure_logger(args.debug, args.log_file)

    logger_queue = multiprocessing.Queue()
    logger_thread = _make_logger_thread(logger_queue)
    logger_thread.start()

    to_ingest = _find_files_to_ingest(args.files)

    worker_processes = []
    files_per_worker = len(to_ingest) // args.num_workers
    file_segments = [to_ingest[i:i + files_per_worker]
                     for i in range(0, len(to_ingest), files_per_worker)]
    for segment in file_segments:
        worker = _make_ingestion_worker(
            files=segment,
            ingester_args={
                'uid': args.uid,
                'source_prefix': args.source_prefix
            },
            logger_args={
                'logger_queue': logger_queue,
                'debug': args.debug,
            }
        )
        worker_processes.append(worker)
        worker.start()

    for worker in worker_processes:
        worker.join()

    logging.info('All ingestion across all workers complete.')

    # Tell the logger thread to stop
    logger_queue.put(None)
    logger_thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Ingest files into ElasticSearch for use with Simon.')

    parser.add_argument(
        '--files',
        nargs='+',
        help='One or more paths to files or folders to be ingested into ElasticSearch. Can be local paths or S3 URIs.'
    )
    parser.add_argument(
        '--uid',
        default='ingest_files',
        help='UID to be associated with ingested files.'
    )
    parser.add_argument(
        '--source_prefix',
        default=None,
        help='Prefix to be prepended to file names when setting `source` attribute for local documents.'
    )
    parser.add_argument(
        '--num_workers',
        type=int,
        default=1,
        help='Number of worker processes to use for ingestion.'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help='Enable debug logging.'
    )
    parser.add_argument(
        '--log_file',
        default=None,
        help='Mirror logs to a file in addition to stdout.'
    )

    args = parser.parse_args()

    main(args)

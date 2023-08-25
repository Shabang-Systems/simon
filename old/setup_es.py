import argparse

from elasticsearch import Elasticsearch

from simon.environment import get_es_config
from simon.components.elastic import _nuke_schema, _seed_schema, _optimize_index


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Setup ElasticSearch for first run.')

    parser.add_argument(
        '--nuke',
        action='store_true',
        help='Nuke any existing ElasticSearch schema/data from simon before recreating.'
    )

    parser.add_argument(
        '--merge',
        action='store_true',
        help='Creating a force merge on the ElasticSearch index to optimize KNN searches.'
    )

    args = parser.parse_args()

    es_config = get_es_config()
    es = Elasticsearch(**es_config, request_timeout=1000000)

    if args.nuke:
        print('Nuking any pre-existing simon indices in ElasticSearch before recreating...')
        _nuke_schema(es)
        print('Nuke complete!')

    if args.merge:
        print("Force merging the ES index...")
        _optimize_index(es)
        print("This will continue to happen in the background after this program exits.")
    else:
        print('Seeding ElasticSearch schema...')
        _seed_schema(es)
        print('Done!')

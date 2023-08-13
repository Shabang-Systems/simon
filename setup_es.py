import argparse

from elasticsearch import Elasticsearch

from simon.environment import get_es_config
from simon.components.elastic import _nuke_schema, _seed_schema


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Setup ElasticSearch for first run.')

    parser.add_argument(
        '--nuke',
        action='store_true',
        help='Nuke any existing ElasticSearch schema/data from simon before recreating.'
    )

    args = parser.parse_args()

    es_config = get_es_config()
    es = Elasticsearch(**es_config)

    if args.nuke:
        print('Nuking any pre-existing simon indices in ElasticSearch before recreating...')
        _nuke_schema(es)
        print('Nuke complete!')

    print('Seeding ElasticSearch schema...')
    _seed_schema(es)

    print('Done!')

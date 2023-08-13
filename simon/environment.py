import os

from dotenv import dotenv_values


def get_es_config(raise_on_missing=False):
    env_config = {
        **dotenv_values('.env'),
        **os.environ,  # Override values loaded from file with those set in shell (if any)
    }

    es_config = {}

    elastic_cloud_id = env_config.get('ELASTIC_CLOUD_ID', None)
    elastic_url = env_config.get('ELASTIC_URL', None)

    if elastic_cloud_id and elastic_url:
        print(
            '**Warning!!!**\n'
            'Both ELASTIC_CLOUD_ID and ELASTIC_URL are set. Using the value from ELASTIC_CLOUD_ID.'
        )
        es_config['cloud_id'] = elastic_cloud_id
    elif elastic_cloud_id:
        es_config['cloud_id'] = elastic_cloud_id
    elif elastic_url:
        es_config['hosts'] = [elastic_url]
    elif raise_on_missing:
        raise RuntimeError('At least one of ELASTIC_URL or ELASTIC_CLOUD_ID must be set in environment variables.')
    else:
        print(
            '**Warning!!!**\n'
            'Neither ELASTIC_URL nor ELASTIC_CLOUD_ID is set. Will use the default value of "http://localhost:9200".'
        )
        es_config['hosts'] = ['http://localhost:9200']
    
    if 'ELASTIC_USER' not in env_config:
        print(
            '**Warning!!!**\n'
            'ELASTIC_USER is not set. Will use the default value of "elastic".'
        )
    if 'ELASTIC_PASSWORD' not in env_config:
        print(
            '**Warning!!!**\n'
            'ELASTIC_PASSWORD is not set. Will pass `None` to ElasticSearch client (which will probably fail).'
        )

    es_config['basic_auth'] = (env_config.get('ELASTIC_USER', 'elastic'), env_config.get('ELASTIC_PASSWORD', None))
    
    return es_config


def get_env_vars(raise_on_missing=False):
    # Entries in this list are required.
    needed = ['OPENAI_KEY']
    # Entries in this list are optional/less important.
    wanted = []
    env_data = {'_MISSING': []}

    config = {
        **dotenv_values('.env'),
        **os.environ,  # Override values loaded from file with those set in shell (if any)
    }

    for var in needed:
        if var in config and config[var]:
            env_data[var] = config[var]
        else:
            env_data[var] = None
            env_data['_MISSING'].append(var)

    missing_vars = ', '.join(env_data['_MISSING'])
    if missing_vars and raise_on_missing:
        missing_vars = ', '.join(env_data['_MISSING'])
        raise RuntimeError(f'Missing required environment variables: {missing_vars}')
    elif missing_vars:
        print(
            '**Warning!!!**\n'
            'Not all required environment variables present, some code might not function properly.\n'
            f'Missing vars: {missing_vars}'
        )

    # Handle ES config separately because it's a bit more complicated
    env_data['ES_CONFIG'] = get_es_config(raise_on_missing=raise_on_missing)

    for var in wanted:
        if var in config and config[var]:
            env_data[var] = config[var]
        else:
            print(
                f'Optional environment variable {var} not set.'
            )
    
    return env_data


if __name__ == '__main__':
    env_data = get_env_vars()
    if not env_data['_MISSING']:
        print('\n[SUCCESS] All required environment variables are set!')

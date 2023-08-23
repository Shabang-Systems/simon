import os

from dotenv import dotenv_values


def get_db_config(raise_on_missing=False):
    env_config = {
        **dotenv_values('.env'),
        **os.environ,  # Override values loaded from file with those set in shell (if any)
    }

    db_config = {}

    db_url = env_config.get('DB_URL', None)
    db_name = env_config.get('DB_NAME', None)


    if elastic_cloud_id and elastic_url:   
    return es_config


def get_env_vars(raise_on_missing=False):
    # Entries in this list are required.
    needed = ['OPENAI_API_KEY']
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

    # Collect OpenAI config into one place
    env_data["OAI_CONFIG"] = {
        "openai_api_key": config["OPENAI_API_KEY"],
        "openai_api_base": config.get("OPENAI_API_BASE", None),
        "openai_api_type": config.get("OPENAI_API_TYPE", None),
        "openai_api_version": config.get("OPENAI_API_VERSION", None),
    }

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

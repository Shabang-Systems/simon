import os

from dotenv import dotenv_values


def get_env_vars(raise_on_missing=False):
    needed = ["OPENAI_KEY", "ELASTIC_URL", "ELASTIC_USER", "ELASTIC_PASSWORD", "GOOGLE_MAPS_KEY"]
    found = []
    missing = []

    config = {
        **dotenv_values(".env"),
        **os.environ,  # Override values loaded from file with those set in shell (if any)
    }

    for var in needed:
        if var in config and config[var]:
            found.append(config[var])
        else:
            found.append(None)
            missing.append(var)

    if missing and raise_on_missing:
        raise RuntimeError(
            "Missing needed environment variables: {}".format(", ".join(missing))
        )
    elif missing:
        print(
            "Not all required environment variables present, some code might not function properly.\n"
            "Missing vars: {}".format(", ".join(missing))
        )
    
    return found, missing


if __name__ == '__main__':
    _, missing = get_env_vars()
    if not missing:
        print('All environment variables are set!')

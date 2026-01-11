import os

from app.configurations.constants import ROOT_DIR


def get_env_type() -> str:
    return os.getenv("ENV_TYPE", "dev")


def get_env_file() -> str:
    match get_env_type():
        case "dev":
            return os.path.join(ROOT_DIR, ".env.local")
        case "prod":
            return os.path.join(ROOT_DIR, ".env.prod")
        case "test":
            return os.path.join(ROOT_DIR, ".env.test") 
        case _:
            raise ValueError(f"Invalid env type: {get_env_type()}") 

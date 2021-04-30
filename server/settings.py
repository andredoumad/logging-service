import os
from dotenv import load_dotenv

load_dotenv()

def get_env(variable_name, default=None):
    value = os.getenv(variable_name)
    if value is None:
        if default is None:
            raise ValueError(f"{variable_name} is not presented in environment variables. Check your .env file")
        else:
            return default
    if str(value).lower() in ("true", "false"):
        return str(value).lower() == "true"
    return value


LOCAL_DEV_MODE = get_env("LOCAL_DEV_MODE")
AWS_ACCESS_KEY = get_env("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = get_env("AWS_SECRET_ACCESS_KEY")
S3_LOGGING = get_env("S3_LOGGING")
Kibana_login = int(get_env("Kibana_login"))

"""
Configuration module
"""
from typing import Union
from dotenv import load_dotenv
import os

load_dotenv()


class AppConfigError(Exception):
    """Configuration error"""
    pass


def _parse_bool(val: Union[str, bool]) -> bool:
    """Parse boolean from string or bool"""
    return val if isinstance(val, bool) else val.lower() in ['true', 'yes', '1']


class AppConfig:
    """Application configuration from .env"""

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 24

    # Auth
    USER: str
    PASS: str

    # Debug
    DEBUG: bool = False

    def __init__(self, env):
        for field, field_type in self.__annotations__.items():
            if not field.isupper():
                continue

            default_value = getattr(self.__class__, field, None)
            env_value = env.get(field)

            if default_value is None and env_value is None:
                raise AppConfigError(f'The {field} field is required in .env')

            try:
                if field_type == bool:
                    value = _parse_bool(env_value if env_value is not None else default_value)
                elif field_type == int:
                    value = int(env_value) if env_value is not None else default_value
                else:
                    value = env_value if env_value is not None else default_value

                setattr(self, field, value)
            except (ValueError, TypeError) as e:
                raise AppConfigError(
                    f'Unable to cast value of "{env_value}" to type "{field_type}" for "{field}" field'
                ) from e

    def __repr__(self):
        return str(self.__dict__)


# Export global Config
Config = AppConfig(os.environ)
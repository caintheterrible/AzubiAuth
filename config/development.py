from functools import lru_cache
from typing import List, Optional
from os import environ
from pathlib import Path
from warnings import warn
import json


class DevelopmentConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


class DevelopmentConfiguration:
    """Development environment-specific configurations."""
    def __init__(self, config_file:Optional[str]=None):
        """
        Initialize development configuration, optionally loading from a file or environment variables.
        Args:
            config_file: Expected path to a JSON configuration file (optional).

        Raises:
            DevelopmentConfigurationError: If configuration values are invalid or the file is malformed.
        """
        # Default values
        self._debug:bool=True
        self._allowed_hosts:List[str]=['127.0.0.1','localhost']
        self._cors_allow_all_origins:bool=True

        # Load from configuration file if provided
        if config_file:
            self._load_from_configuration_file(config_file)

        # Override with environment variables if present
        self._load_from_env()

    def _load_from_configuration_file(self, config_file:str)->None:
        """
        Loads configuration from JSON configuration files.
        :param config_file: Expected JSON configuration file
        :return: None
        """
        try:
            config_path=Path(config_file)
            if not config_path.exists():
                raise DevelopmentConfigurationError(f"Configuration file not found: '{config_file}'")
            with config_path.open('r') as file:
                config=json.load(file)
                self._debug=config.get('debug', self._debug)
                self._allowed_hosts=config.get('allowed_hosts', self._allowed_hosts)
                self._cors_allow_all_origins=config.get('cors_allow_all_origins', self._cors_allow_all_origins)

        except json.JSONDecodeError as decode_err:
            raise DevelopmentConfigurationError(f"Invalid JSON in configuration file: {decode_err}")
        except Exception as exc:
            raise DevelopmentConfigurationError(f"Error loading configuration file: {exc}")

    def _load_from_env(self)->None:
        """Overrides defaults with environment variables if they exist."""
        self._debug=environ.get('DEV_DEBUG', str(self._debug)).lower()=='true'
        if 'DEV_ALLOWED_HOSTS' in environ:
            self._allowed_hosts=environ['DEV_ALLOWED_HOSTS'].split(',')
        self._cors_allow_all_origins=environ.get(
            'DEV_CORS_ALLOW_ALL_ORIGINS', str(self._cors_allow_all_origins)
        ).lower()=='true'

    # to be reconfigured to trace error types instead
    def _validate(self)->None:
        """Validates configuration values."""
        if not isinstance(self._debug, bool):
            raise DevelopmentConfigurationError('DEBUG must be a boolean.')
        if not isinstance(self._allowed_hosts, list) or not all(isinstance(h, str) and h.strip() for h in self._allowed_hosts):
            raise DevelopmentConfigurationError('ALLOWED_HOSTS must be a string.')
        if not isinstance(self._cors_allow_all_origins, bool):
            raise DevelopmentConfigurationError('CORS_ALLOW_ALL_ORIGINS must be a boolean value.')

        if self._cors_allow_all_origins:
            warn("CORS_ALLOW_ALL_ORIGINS is set to True, which is insecure. Use cautiously.")

    # def __setattr__(self, name:str, value:any)->None:
    #     """Prevent modification of configuration attributes after initialization."""
    #     if name.startswith('_') and hasattr(self, name):
    #         raise AttributeError('Configuration attributes are immutable after initialization.')
    #     super().__setattr__(name, value)

    @property
    def debug(self)->bool:
        """Debug mode status. Set to True only in development and testing environments."""
        return self._debug

    @property
    def allowed_hosts(self)->List[str]:
        """List of allowed hosts for the application."""
        return self._allowed_hosts[:]

    @property
    def cors_allow_all_origins(self)->bool:
        """CORS setting to allow all origins. Disabled temporarily in development environments only."""
        return self._cors_allow_all_origins


# Temporary singleton configuration. To modify configurations to factory later for better instance management
@lru_cache(maxsize=1)
def get_development_configurations(config_file:Optional[str]=None)->DevelopmentConfiguration:
    """
    Retrieves cached instance of DevelopmentConfiguration.
    :param config_file: Optional path to a JSON configuration file.
    :return: DevelopmentConfiguration: A configured instance of development settings.
    """
    return DevelopmentConfiguration(config_file)


development_configurations:DevelopmentConfiguration=get_development_configurations()
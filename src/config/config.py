import yaml
import os

class Config:
    def __init__(self, environment='DEVELOPMENT', yaml_file='config.yml'):
        self.environment = environment
        self.config = self._get_config(environment)
        self._populate_attributes()

    def _get_config(self,enviroment):
        """Load the YAML configuration file."""
        config_ = self._load_yaml(yaml_file='config.yml')
        config_db = self._load_yaml(yaml_file='db_config.yml',environment=enviroment)
        # config_ftp = self._load_yaml(yaml_file='ftp_config.yml',environment=enviroment)
        # stah_config_ftp = self._load_yaml(yaml_file='stah_ftp_config.yml',environment=enviroment)
        config = {**config_, **config_db}
        return config

    def _load_yaml(self, yaml_file, environment = None):
        """Load the YAML configuration file."""
        base_dir_config = os.path.abspath(os.path.dirname(__file__))
        yaml_file = os.path.join(base_dir_config,yaml_file)
        with open(yaml_file, 'r') as file:
            config = yaml.safe_load(file)

        if environment == None:
            return config
        else:
            return config.get(environment, {})

    def _get_value(self, key, default=None):
        """Retrieve a config value, checking for environment variable substitution."""
        value = self.config.get(key, default)
        if isinstance(value, str) and value.startswith('${'):
            env_var = value[2:-1]  # Strip ${ and }
            return os.getenv(env_var, default)
        return value

    def _populate_attributes(self):
        """Automatically turn config keys into class attributes."""
        for key, value in self.config.items():
            setattr(self, key, self._get_value(key))

    def __repr__(self):
        """For better debugging, print the config as attributes."""
        return f"Config({', '.join(f'{k}={v}' for k, v in self.config.items())})"



if __name__ == "__main__":
    config = Config(environment='DEVELOPMENT')
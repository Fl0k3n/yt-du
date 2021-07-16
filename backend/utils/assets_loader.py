import dotenv
from pathlib import Path


class AssetsLoader:
    _PARENT_DIR = Path(__file__).absolute().parent.parent
    _ASSETS_DIR_NAME = 'assets'
    _ASSETS_PATH = Path.joinpath(_PARENT_DIR, _ASSETS_DIR_NAME).absolute()
    _CONFIG = dotenv.dotenv_values(Path.joinpath(_ASSETS_PATH, '.env'))

    @classmethod
    def get_env(cls, var: str):
        return cls._CONFIG.get(var)

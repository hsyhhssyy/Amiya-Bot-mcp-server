#src/app/context.py
from src.config.model import Config
from src.data.repository.data_repository import OperatorRepository

class AppContext:
    def __init__(self, cfg: Config):
        self.operator_repo = OperatorRepository()
        pass


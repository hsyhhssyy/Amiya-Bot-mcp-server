from dataclasses import dataclass
from typing import Any, Dict, List

from src.data.loader.json_file_loader import JsonFileLoader
from src.data.models.operator_impl import OperatorImpl
from src.domain.models.operator import Operator
from src.helpers.bundle_helper import *


@dataclass(frozen=True, slots=True)
class DataBundle:
    version: str

    # domain models
    operators: Dict[str, Operator]
    tokens: Dict[str, Any]  # 如果你有 domain Token，就改成 Dict[str, Token]

    # indices
    operator_name_to_id: Dict[str, str]
    operator_index_to_id: Dict[str, str]

    # 可选：保留一些表，方便详情方法内部使用（避免再读磁盘）
    tables: Dict[str, Any]

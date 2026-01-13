# domain/models/operator.py
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any

STR_DICT = Dict[str, Any]
LIST_STR_DICT = List[STR_DICT]

class Operator(ABC):
    """
    干员领域模型（接口定义）
    """

    def __init__(self):
        # ---- 基础标识 ----
        self.id: str = ""
        self.name: str = ""
        self.en_name: str = ""
        self.wiki_name: str = ""
        self.index_name: str = ""
        self.origin_name: str = ""

        # ---- 分类与属性 ----
        self.rarity: int = 0
        self.classes: str = ""
        self.classes_sub: str = ""
        self.classes_code: str = ""
        self.type: str = ""
        self.tags: List[str] = []
        self.range: str = ""

        # ---- 人物信息 ----
        self.sex: str = ""
        self.race: str = ""
        self.cv: Dict[str, str] = {}
        self.drawer: str = ""

        # ---- 阵营 ----
        self.team_id: str = ""
        self.team: str = ""
        self.group_id: str = ""
        self.group: str = ""
        self.nation_id: str = ""
        self.nation: str = ""

        # ---- 其他 ----
        self.birthday: str = ""
        self.profile: str = ""
        self.impression: str = ""
        self.potential_item: str = ""

        self.limit: bool = False
        self.unavailable: bool = False
        self.is_recruit: bool = False
        self.is_classic: bool = False
        self.is_sp: bool = False

    # ========== 对外稳定接口 ==========

    @abstractmethod
    def summary(self) -> STR_DICT:
        """用于列表/简略展示"""
        raise NotImplementedError

    @abstractmethod
    def detail(self) -> STR_DICT:
        """完整详情（不含资源文件）"""
        raise NotImplementedError

    @abstractmethod
    def talents(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def skills(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def modules(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def skins(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def voices(self) -> LIST_STR_DICT:
        raise NotImplementedError

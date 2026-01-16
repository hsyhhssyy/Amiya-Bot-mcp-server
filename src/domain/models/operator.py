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
        """干员 ID（唯一标识符）"""
        self.name: str = ""
        """干员名称"""
        self.en_name: str = ""
        """干员英文名"""
        self.wiki_name: str = ""
        """干员维基名称"""
        self.index_name: str = ""
        """干员索引名称（无标点）"""
        self.origin_name: str = ""
        """干员真名（如果有）"""

        # ---- 分类与属性 ----
        self.rarity: int = 0
        """干员稀有度（1-6）"""
        self.classes: str = ""
        """干员职业（中文）, 如“先锋”"""
        self.classes_sub: str = ""
        """干员子职业（中文）, 如“领主”"""
        self.classes_code: str = ""
        """干员职业代码，如“VANGUARD”"""
        self.type: str = ""
        """干员类型（中文）, 如“近战位”"""
        self.tags: List[str] = []
        """干员标签列表，如“新手”、“召唤”"""
        self.range: str = ""
        """干员攻击范围描述"""

        # ---- 人物信息 ----
        self.sex: str = ""
        """性别"""
        self.race: str = ""
        """种族"""
        self.cv: Dict[str, str] = {}
        """声优信息，格式如 {"中文": "某某", "日文": "某某"}，如果存在多个声优则以半角逗号分隔"""
        self.drawer: str = ""
        """画师"""

        # ---- 阵营 ----
        self.team_id: str = ""
        """主阵营 ID"""
        self.team: str = ""
        self.nation_id: str = ""
        """国家/势力 ID"""
        self.group_id: str = ""
        """集团 ID"""
        self.group: str = ""
        """主阵营名称"""
        self.nation_id: str = ""
        """国家/势力 ID"""
        self.nation: str = ""
        """国家/势力 名称"""

        # ---- 其他 ----
        self.birthday: str = ""
        """生日，格式如 "MM-DD" """
        self.profile: str = ""
        """干员档案/简介"""
        self.impression: str = ""
        """干员印象"""
        self.potential_item: str = ""
        """潜能物品"""

        self.limit: bool = False
        """是否为限定干员"""
        self.unavailable: bool = False
        """是否为不可获取干员"""
        self.is_recruit: bool = False
        """是否可通过公开招募获取"""
        self.is_classic: bool = False
        """是否为中坚干员"""
        self.is_sp: bool = False
        """是否为特殊干员"""

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

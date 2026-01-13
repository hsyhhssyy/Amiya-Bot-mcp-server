from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable, Awaitable

from src.app.context import AppContext
from src.data.models.bundle import DataBundle
from src.data.loader.json_file_loader import JsonFileLoader
from src.data.loader.git_gamedata_maintainer import GitGameDataMaintainer
from src.data.models.operator_impl import OperatorImpl
from src.domain.models.operator import Operator
from src.domain.models.token import Token
from src.helpers.bundle_helper import *

log = logging.getLogger(__name__)


class DataNotReadyError(RuntimeError):
    """数据尚未准备好（内存中没有 bundle）"""


@dataclass(slots=True)
class DataRepository:
    """
    DataRepository：持有当前 DataBundle（只读快照）并提供刷新能力。

    - 不建议在 get_bundle() 里做 IO
    - ensure_ready()/refresh_from_disk() 才做 IO（通常在启动或维护任务中调用）
    """

    json_loader: JsonFileLoader

    # 维护器（git pull/clone + unzip）
    maintainer: Optional[GitGameDataMaintainer] = None

    # 内部状态
    _bundle: Optional[DataBundle] = None
    _ready_lock: asyncio.Lock = asyncio.Lock()
    _update_lock: asyncio.Lock = asyncio.Lock()

    context : AppContext

    def is_ready(self) -> bool:
        return self._bundle is not None

    def get_bundle(self) -> DataBundle:
        """
        高频读：直接返回当前快照（不加锁）。
        如果你保证启动阶段已经 ensure_ready()，业务里就不会报错。
        """
        if self._bundle is None:
            raise DataNotReadyError("Game data bundle is not ready. Call ensure_ready() first.")
        return self._bundle

    async def ensure_ready(self) -> DataBundle:
        """
        懒加载：当 _bundle 为空时，从磁盘加载一次（并发安全）。
        注意：这里只读磁盘，不做 git 更新/解压。
        """
        if self._bundle is not None:
            return self._bundle

        async with self._ready_lock:
            if self._bundle is not None:
                return self._bundle

            log.info("Loading game data bundle from disk...")
            bundle = await asyncio.to_thread(self._load_bundle)
            self._bundle = bundle
            log.info("Game data bundle loaded. version=%s", getattr(bundle, "version", ""))
            return bundle

    async def refresh_from_disk(self) -> DataBundle:
        """
        强制从磁盘重载并原子替换内存快照。
        """
        async with self._update_lock:
            log.info("Refreshing game data bundle from disk...")
            bundle = await asyncio.to_thread(self._load_bundle)
            self._bundle = bundle  # 原子替换
            # 数据刷新后，建议清一下 json loader 的 cache
            self.json_loader.clear_cache()
            log.info("Game data bundle refreshed. version=%s", getattr(bundle, "version", ""))
            return bundle

    async def update_and_refresh(self) -> bool:
        """
        可选：执行维护任务（git pull/clone + unzip），成功后 refresh_from_disk。
        这是给“定时维护任务”用的。
        """
        if self.maintainer is None:
            log.warning("No maintainer configured; skip update.")
            return False

        async with self._update_lock:
            # 维护任务是阻塞 IO，丢到线程里
            log.info("Updating gamedata on disk (git+zip)...")
            ok = await asyncio.to_thread(self.maintainer.update)
            if not ok:
                log.warning("Update gamedata on disk failed.")
                return False

            log.info("Update ok. Reloading bundle into memory...")
            bundle = await asyncio.to_thread(self._load_bundle)
            self._bundle = bundle
            self.json_loader.clear_cache()
            log.info("Bundle reloaded after update. version=%s", getattr(bundle, "version", ""))
            return True

    def _load_bundle(self) -> DataBundle:
        """
        同步方法：从 json_loader 构建 bundle。
        放到 to_thread 里调用，避免阻塞 event loop。
        """
        return self._load_bundle_from_loader()

    
    def _load_bundle_from_loader(self) -> DataBundle:
        """
        - 从 JsonFileLoader 读取必要的表
        - 构建 OperatorImpl / TokenImpl（domain objects）
        - 构建索引
        - 返回 DataBundle

        你可以在 DataRepository 的 ensure_ready/refresh_from_disk 中调用它。
        """

        # 1) 读取表（缺失就给默认值，确保 loader 不报错）
        tables: Dict[str, Any] = {}
        for name, folder in [
            ("character_table", "excel"),
            ("uniequip_table", "excel"),
            ("handbook_team_table", "excel"),
            ("item_table", "excel"),
            ("range_table", "excel"),
            ("skill_table", "excel"),
            ("charword_table", "excel"),
            ("char_meta_table", "excel"),
            # 你后面需要再加：handbook_info_table / skin_table / building_data / battle_equip_table ...
        ]:
            tables[name] = self.json_loader.read_json(name, folder=folder) or {}

        character_table: Dict[str, dict] = tables["character_table"] or {}

        # 2) 构建 Token（旧项目 Token 从 character_table 的某些条目来，这里给一个“可运行”的策略）
        #    你可以按自己实际数据规则调整 token 的筛选条件
        tokens: Dict[str, Token] = {}
        range_table = tables.get("range_table") or {}

        for code, data in character_table.items():
            # 一个非常保守的判定：token 往往没有 displayNumber，且很多 token id 不是 char_ 开头
            # 你可以更精确：比如 data.get("isNotObtainable") 或 profession/position 特征等
            if not isinstance(data, dict):
                continue
            if str(code).startswith("token_") or data.get("profession") == "TOKEN":
                phases = data.get("phases") or []
                attrs: List[Dict[str, Any]] = []
                for evolve, ph in enumerate(phases):
                    rid = ph.get("rangeId")
                    grids = range_table.get(rid, {}).get("grids")
                    range_map = build_range(grids) if grids else "无范围"
                    attrs.append({"evolve": evolve, "range": range_map, "attr": ph.get("attributesKeyFrames")})
                tokens[code] = Token(
                    id=code,
                    name=data.get("name", ""),
                    en_name=data.get("appellation", ""),
                    description=html_tag_format(data.get("description") or ""),
                    classes=getattr(self.context.cfg, "token_classes", {}).get(data.get("profession"), "未知"),
                    type=getattr(self.context.cfg, "types", {}).get(data.get("position"), "未知"),
                    attr=attrs,
                )

        # 3) 构建 Operator domain objects + 索引
        operators: Dict[str, Operator] = {}
        name_to_id: Dict[str, str] = {}
        index_to_id: Dict[str, str] = {}

        for op_id, data in character_table.items():
            if not isinstance(data, dict):
                continue

            # 旧项目里 operator_table 是 character_table 的“干员条目”部分，这里做一个基础过滤：
            # 排除明显不是干员的数据（你可按实际规则完善）
            if not str(op_id).startswith("char_"):
                continue

            op = OperatorImpl(op_id, data, cfg=self.context.cfg, tables=tables, is_recruit=False)
            operators[op_id] = op

            if op.name:
                name_to_id[op.name] = op_id
            if op.en_name:
                name_to_id[op.en_name] = op_id
            if op.index_name:
                index_to_id[op.index_name] = op_id

        # 4) version：如果你有 version.json 或 git commit hash，可以在这里读
        version = "unknown"

        return DataBundle(
            version=version,
            operators=operators,
            tokens=tokens,
            operator_name_to_id=name_to_id,
            operator_index_to_id=index_to_id,
            tables=tables,
        )
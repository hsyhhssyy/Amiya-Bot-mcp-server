from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.model import Config
from src.data.loader._git_gamedata_maintainer import GitGameDataMaintainer
from src.data.models.bundle import DataBundle
from src.data.models._operator_impl import OperatorImpl
from src.domain.models.operator import Operator
from src.domain.models.token import Token
from src.helpers.bundle_helper import build_range, html_tag_format

log = logging.getLogger(__name__)


class DataNotReadyError(RuntimeError):
    """数据尚未准备好（内存中没有 bundle）"""

@dataclass(slots=True)
class DataRepository:
    """
    DataRepository：持有当前 DataBundle（只读快照）并提供刷新能力。

    - get_bundle() 不做 IO
    - startup_prepare()/refresh_from_disk()/ensure_ready() 才做 IO
    """

    cfg: Config

    _maintainer: Optional[GitGameDataMaintainer] = field(default=None, init=False, repr=False)
    _bundle: Optional[DataBundle] = field(default=None, init=False, repr=False)

    _ready_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    _update_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    def __post_init__(self):
        # 约定：cfg.GameDataPath 指向解包数据根目录（里面有 excel/character_table.json 等）
        data_root = Path(self.cfg.GameDataPath)

        # maintainer 的根目录/参数你要确保与 update() 的实现一致
        # 这里按你原来写法：把 repo 拉到 GameDataPath 的父目录
        self._maintainer = GitGameDataMaintainer(self.cfg.GameDataRepo, data_root.parent)

    # ---------- public ----------

    def is_ready(self) -> bool:
        return self._bundle is not None

    def get_bundle(self) -> DataBundle:
        if self._bundle is None:
            raise DataNotReadyError("Game data bundle is not ready. Call startup_prepare()/ensure_ready() first.")
        return self._bundle

    async def startup_prepare(self, force_update_on_first_run: bool = True) -> DataBundle:
        if self._maintainer is None:
            raise RuntimeError("No maintainer configured; cannot perform startup_prepare.")

        if force_update_on_first_run and not self._maintainer.is_initialized():
            log.info("No local gamedata found. Performing first-time git update...")
            ok = await asyncio.to_thread(self._maintainer.update)
            if not ok:
                raise RuntimeError("First-time gamedata update failed.")
            log.info("First-time gamedata update done.")

        return await self.refresh_from_disk()

    async def ensure_ready(self) -> DataBundle:
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
        async with self._update_lock:
            log.info("Refreshing game data bundle from disk...")
            bundle = await asyncio.to_thread(self._load_bundle)
            self._bundle = bundle
            log.info("Game data bundle refreshed. version=%s", getattr(bundle, "version", ""))
            return bundle

    async def update_and_refresh(self) -> bool:
        if self._maintainer is None:
            log.warning("No maintainer configured; skip update.")
            return False

        async with self._update_lock:
            log.info("Updating gamedata on disk (git+zip)...")
            ok = await asyncio.to_thread(self._maintainer.update)
            if not ok:
                log.warning("Update gamedata on disk failed.")
                return False

            log.info("Update ok. Reloading bundle into memory...")
            bundle = await asyncio.to_thread(self._load_bundle)
            self._bundle = bundle
            log.info("Bundle reloaded after update. version=%s", getattr(bundle, "version", ""))
            return True

    # ---------- internal ----------

    def _read_json(self, name: str, folder: str) -> Dict[str, Any]:
        """
        直接读取文件：<GameDataPath>/<folder>/<name>.json
        读不到/解析失败则返回 {}
        """
        path = Path(folder) / f"{name}.json"
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            log.exception("Failed to read json: %s", path)
            return {}

    def _load_bundle(self) -> DataBundle:
        return self._load_bundle_from_disk()

    def _load_bundle_from_disk(self) -> DataBundle:
        # 1) 读取表
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
        ]:
            exact_folder = Path(self.cfg.GameDataPath) / folder
            tables[name] = self._read_json(name, str(exact_folder)) or {}

        # 2) 添加常量表
        tables["token_classes"] = {"TOKEN": "召唤物", "TRAP": "装置"}
        tables["types"] = {"ALL": "不限部署位", "MELEE": "近战位", "RANGED": "远程位"}
        tables["classes"] = {
            "CASTER": "术师",
            "MEDIC": "医疗",
            "PIONEER": "先锋",
            "SNIPER": "狙击",
            "SPECIAL": "特种",
            "SUPPORT": "辅助",
            "TANK": "重装",
            "WARRIOR": "近卫",
        }
        tables["high_star"] = {"5": "资深干员", "6": "高级资深干员"}
        tables["html_symbol"] = {
            "<替身>": "替身",
            "<支援装置>": "支援装置",
        }

        tables["sp_type"] = {
            "INCREASE_WITH_TIME": "自动回复",
            "INCREASE_WHEN_ATTACK": "攻击回复",
            "INCREASE_WHEN_TAKEN_DAMAGE": "受击回复",
            1: "自动回复",
            2: "攻击回复",
            4: "受击回复",
            8: "被动",
        }

        tables["skill_type"] = {
            "PASSIVE": "被动",
            "MANUAL": "手动触发",
            "AUTO": "自动触发",
            0: "被动",
            1: "手动触发",
            2: "自动触发",
        }

        tables["skill_level"] = {
            1: "等级1",
            2: "等级2",
            3: "等级3",
            4: "等级4",
            5: "等级5",
            6: "等级6",
            7: "等级7",
            8: "等级8（专精1）",
            9: "等级9（专精2）",
            10: "等级10（专精3）",
        }

        tables["attrs"] = {
            "maxHp": "最大生命值",
            "atk": "攻击力",
            "def": "防御力",
            "magicResistance": "魔法抗性",
            "attackSpeed": "攻击速度",
            "baseAttackTime": "攻击间隔",
            "blockCnt": "阻挡数",
            "cost": "部署费用",
            "respawnTime": "再部署时间",
        }

        tables["attrs_unit"] = {
            "baseAttackTime": "秒",
            "respawnTime": "秒",
        }


        # 添加本地表
        # 将 ProjectRoot/data/tables 下的所有 json 文件读入 tables
        local_tables_path = Path(self.cfg.ProjectRoot) / "data" / "local"
        if local_tables_path.exists() and local_tables_path.is_dir():
            for file in local_tables_path.glob("*.json"):
                table_name = file.stem
                tables["local_"+table_name] = self._read_json(table_name, str(local_tables_path)) or {}

        tables["limit"] = []
        tables["unavailable"] = []

        character_table: Dict[str, dict] = tables.get("character_table") or {}
        range_table: Dict[str, Any] = tables.get("range_table") or {}

        # 3) 构建 Token
        tokens: Dict[str, Token] = {}
        token_classes = tables.get("token_classes", {}) or {}
        types = tables.get("types", {}) or {}

        for code, data in character_table.items():
            if not isinstance(data, dict):
                continue
            if str(code).startswith("token_") or data.get("profession") == "TOKEN":
                phases = data.get("phases") or []
                attrs: List[Dict[str, Any]] = []
                for evolve, ph in enumerate(phases):
                    rid = ph.get("rangeId")
                    grids = (range_table.get(rid) or {}).get("grids")
                    range_map = build_range(grids) if grids else "无范围"
                    attrs.append(
                        {"evolve": evolve, "range": range_map, "attr": ph.get("attributesKeyFrames")}
                    )

                tokens[code] = Token(
                    id=code,
                    name=data.get("name", ""),
                    en_name=data.get("appellation", ""),
                    description=html_tag_format(data.get("description") or ""),
                    classes=token_classes.get(data.get("profession"), "未知"),
                    type=types.get(data.get("position"), "未知"),
                    attr=attrs,
                )

        # 4) 构建 Operator + 索引
        operators: Dict[str, Operator] = {}
        name_to_id: Dict[str, str] = {}
        index_to_id: Dict[str, str] = {}

        for op_id, data in character_table.items():
            if not isinstance(data, dict):
                continue
            if not str(op_id).startswith("char_"):
                continue

            op = OperatorImpl(op_id, data, tables=tables, is_recruit=False)
            operators[op_id] = op

            if getattr(op, "name", ""):
                name_to_id[op.name] = op_id
            if getattr(op, "en_name", ""):
                name_to_id[op.en_name] = op_id
            if getattr(op, "index_name", ""):
                index_to_id[op.index_name] = op_id

        # 5) version（你可以以后改成读取 version.json 或 git commit）
        version = "unknown"

        return DataBundle(
            version=version,
            operators=operators,
            tokens=tokens,
            operator_name_to_id=name_to_id,
            operator_index_to_id=index_to_id,
            tables=tables,
        )

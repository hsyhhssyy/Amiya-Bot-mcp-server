from typing import Dict
from ...domain.models.operator import Operator, STR_DICT, LIST_STR_DICT
from ...helpers.bundle import *

class OperatorImpl(Operator):
    def __init__(
        self,
        op_id: str,
        data: dict,
        tables: Dict[str, Any],
        is_recruit: bool = False,
    ):
        super().__init__()

        sub_classes = get_table(tables, "uniequip_table", source="gamedata", default={}).get("subProfDict", {})
        character_table = get_table(tables, "character_table", source="gamedata", default={})
        team_table = get_table(tables, "handbook_team_table", source="gamedata", default={})
        items = get_table(tables, "item_table", source="gamedata", default={}).get("items", {})

        data["name"] = (data.get("name") or "").strip()

        self.id = op_id

        # type / rarity / number
        pos = data.get("position")
        self.type = get_table(tables, "types", source="local", default={}).get(pos, "未知")

        rarity_raw = data.get("rarity", 0)
        if isinstance(rarity_raw, str):
            # "TIER_5" 之类
            try:
                self.rarity = int(rarity_raw.split("_")[-1])
            except Exception:
                self.rarity = 0
        else:
            # 有些表是 0-based
            self.rarity = int(rarity_raw) + 1 if isinstance(rarity_raw, int) else 0

        self.number = str(data.get("displayNumber") or "")

        # name / en_name
        self.name = data.get("name") or ""
        self.en_name = data.get("appellation") or ""
        self.wiki_name = self.name
        self.index_name = remove_punctuation(self.name)
        self.origin_name = "未知"

        # classes
        prof = data.get("profession")
        self.classes_code = prof or ""
        self.classes = get_table(tables, "classes", source="local", default={}).get(prof, "未知")

        sub_prof_id = data.get("subProfessionId")
        self.classes_sub = sub_classes.get(sub_prof_id, {}).get("subProfessionName", "未知")

        # faction/team/group/nation
        self.team_id = str(data.get("teamId") or "")
        self.team = team_table.get(self.team_id, {}).get("powerName", "未知") if self.team_id else "未知"

        self.group_id = str(data.get("groupId") or "")
        self.group = team_table.get(self.group_id, {}).get("powerName", "未知") if self.group_id else "未知"

        nation_id = character_table.get(op_id, {}).get("nationId")
        self.nation_id = str(nation_id or "")
        self.nation = team_table.get(self.nation_id, {}).get("powerName", "未知") if self.nation_id else "未知"

        # profile / impression
        self.profile = data.get("itemUsage") or "无"
        self.impression = data.get("itemDesc") or "无"

        # potential_item
        self.potential_item = ""
        pid = data.get("potentialItemId")
        if pid and pid in items:
            self.potential_item = items[pid].get("description", "")

        # flags
        self.limit = self.name in get_table(tables, "limit", source="amiyabot", default=[])
        self.unavailable = self.name in get_table(tables, "unavailable", source="amiyabot", default=[])

        self.is_recruit = is_recruit
        self.is_classic = bool(data.get("classicPotentialItemId"))
        self.is_sp = bool(data.get("isSpChar"))

        # tags / range / drawer / cv / origin 等：这里做“轻量初始化”
        self._init_tags(data, tables)
        self._init_range(data, tables)
        self.cv = {}
        self._init_cv(tables)
        self._init_origin(character_table, data, tables)
        self._init_detail(data, tables)
        self._init_talents(data, tables)
        self._init_skills(data, tables)

    def _init_tags(self, data, tables):
        tags = [self.classes, self.type]
        hs = get_table(tables, "rarity_tags", source="local", default={})
        if str(self.rarity) in hs:
            tags.append(hs[str(self.rarity)])
        self.tags = (data.get("tagList") or []) + tags

    def _init_range(self, data, tables):
        # 旧逻辑：取最后 phase 的 rangeId
        range_table = get_table(tables, "range_table", source="gamedata", default={})
        phases = data.get("phases") or []
        if not phases:
            self.range = "无范围"
            return
        range_id = phases[-1].get("rangeId")
        grids = range_table.get(range_id, {}).get("grids")
        self.range = build_range(grids) if grids else "无范围"

    def _init_cv(self, tables):
        word_data = get_table(tables, "charword_table", source="gamedata", default={})
        # 按旧逻辑读取 voiceLangDict
        vdict = (word_data.get("voiceLangDict") or {}).get(self.id, {}).get("dict", {})
        vtype = word_data.get("voiceLangTypeDict") or {}
        if vdict and vtype:
            self.cv = {vtype.get(k, {}).get("name", k): v.get("cvName", "") for k, v in vdict.items()}

    def _init_origin(self, character_table: dict, data, tables):
        sp_char_groups = get_table(tables, "char_meta_table", source="local", default={}).get("spCharGroups") or {}
        for oid, group in sp_char_groups.items():
            if self.id in (group or []):
                self.origin_name = character_table.get(oid, {}).get("name", "未知")
                return

    # ------------------ domain 接口实现（先做可用版，复杂聚合可逐步补齐） ------------------
    def summary(self) -> STR_DICT:
        return {
            "id": self.id,
            "name": self.name,
            "en_name": self.en_name,
            "rarity": self.rarity,
            "classes": self.classes,
            "classes_sub": self.classes_sub,
            "classes_code": self.classes_code,
            "type": self.type,
        }

    def _init_detail(self,data,tables):
        # 你旧项目 detail() 返回 (detail, favor) 两份；这里先合成一份 dict
        items = get_table(tables, "item_table", source="gamedata", default={}).get("items", {})
        token_id = "p_" + self.id
        token = items.get(token_id)

        phases = data.get("phases") or []
        max_level = ""
        max_attr = {}
        if phases:
            max_phases = phases[-1]
            max_level = f"{len(phases)-1} - {max_phases.get('maxLevel', '')}"
            kfs = (max_phases.get("attributesKeyFrames") or [])
            if kfs:
                max_attr = (kfs[-1].get("data") or {})

        trait = html_tag_format(data.get("description") or "")
        if data.get("trait"):
            cand = (data["trait"].get("candidates") or [])
            if cand:
                max_trait = cand[-1]
                trait = parse_template(max_trait.get("blackboard") or [], max_trait.get("overrideDescripton") or trait)

        out = {
            "operator_trait": trait.replace("\\n", "\n"),
            "operator_usage": data.get("itemUsage") or "",
            "operator_quote": data.get("itemDesc") or "",
            "operator_token": token.get("description", "") if token else "",
            "max_level": max_level,
            **max_attr,
        }

        self._detail = out
    
    def detail(self) -> STR_DICT:
        return self._detail

    def _init_talents(self, data, tables):
        talents = []
        for item in data.get("talents") or []:
            cand = item.get("candidates") or []
            if cand:
                max_item = cand[-1]
                talents.append({"talents_name": max_item.get("name", ""), "talents_desc": html_tag_format(max_item.get("description", ""))})
        self._talents = talents

    def talents(self) -> LIST_STR_DICT:
        return self._talents

    def _init_skills(self, data, tables):
        # 这里给一个“简版”，保留你后续扩展空间
        skill_table = tables.get("skill_table") or {}
        out = []
        for idx, sk in enumerate(data.get("skills") or []):
            sid = sk.get("skillId")
            if not sid or sid not in skill_table:
                continue
            detail = skill_table[sid]
            icon = detail.get("iconId") or detail.get("skillId") or sid
            out.append({"skill_no": sid, "skill_index": idx + 1, "skill_name": (detail.get("levels") or [{}])[0].get("name", ""), "skill_icon": icon})
        self._skills = out

    def skills(self) -> LIST_STR_DICT:
        return self._skills

    def modules(self) -> LIST_STR_DICT:
        # 旧项目 modules() 依赖 uniequip_table/battle_equip_table，先给空，后续可按旧逻辑补齐
        return []

    def skins(self) -> LIST_STR_DICT:
        # 旧项目 skins() 依赖 Collection 皮肤列表；你可以把 skins 表在 load_bundle 阶段预处理塞进 tables，再在这里生成
        return []

    def voices(self) -> LIST_STR_DICT:
        return []



from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

from ...domain.models.operator import Operator
from ...app.context import AppContext
from ..bundle import *

@dataclass(frozen=True)
class MatchResult:
    key: str              # name / skin / group ...
    matched_text: str     # 匹配到的关键词（比如 “史尔特尔”）
    value: Any            # 关联对象（比如 Operator / skin_id / group_id）
    score: float = 0.0    # 可选：相似度得分（如果你的 find_most_similar 能返回）

@dataclass
class SearchResults:
    matches: List[MatchResult]

    @property
    def first(self) -> Optional[MatchResult]:
        return self.matches[0] if self.matches else None

    def by_key(self, key: str) -> List[MatchResult]:
        return [m for m in self.matches if m.key == key]

@dataclass(frozen=True)
class SourceSpec:
    key: str
    candidates: Callable[[], Sequence[str]]          # 候选词列表
    resolve: Callable[[str], Any]                    # 命中词 -> 关联对象

def search_info(
    message: str,
    ctx: "AppContext",
    source_keys: Optional[List[str]] = None,
    *,
    similar_mode: bool = True
) -> SearchResults:

    if ctx.data_repository is None:
        return SearchResults(matches=[])

    bundle = ctx.data_repository.get_bundle()

    # 这里把所有 source 的“候选词 + 命中后如何取值”统一起来
    sources: List[SourceSpec] = [
        SourceSpec(
            key="name",
            candidates=lambda: list(bundle.operator_name_to_id.keys()),
            resolve=lambda k: bundle.operator_name_to_id[k],
        ),
        # 以后加 skin/group/voice/story 就继续往下 append
        # SourceSpec(key="skin", candidates=..., resolve=...),
    ]

    # 只扫描用户指定的 keys（保持顺序）
    if source_keys is not None:
        sources = [s for s in sources if s.key in source_keys]

    match_method = find_most_similar if similar_mode else find_longest

    matches: List[MatchResult] = []

    msg_norm = remove_punctuation(message)

    for src in sources:
        cand = src.candidates()
        res = match_method(message, cand)

        if not res:
            continue

        # 我不理解为什么要反查一下，兔妈的代码里有这步，但看起来没啥意义
        # 一个更模糊的搜索不是更好？
        # if remove_punctuation(res) not in msg_norm:
        #     continue

        value = src.resolve(res)
        matches.append(MatchResult(key=src.key, matched_text=res, value=value))

    return SearchResults(matches=matches)

import json, logging
from pathlib import Path
from typing import Any, Dict, Optional

log = logging.getLogger("asset")

class JsonFileLoader:
    def __init__(self, gamedata_dir: Path):
        self.gamedata_dir = gamedata_dir
        self._cache: Dict[str, Dict[str, Any]] = {}

    def read_json(self, name: str, folder: str = "excel") -> Dict[str, Any]:
        key = f"{folder}/{name}"
        if key in self._cache:
            return self._cache[key]

        json_path = self.gamedata_dir / folder / f"{name}.json"
        if not json_path.exists():
            return {}

        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self._cache[key] = data
        return data

    def clear_cache(self, name: Optional[str] = None, folder: str = "excel"):
        if name is None:
            self._cache.clear()
        else:
            self._cache.pop(f"{folder}/{name}", None)

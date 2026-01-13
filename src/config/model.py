import json
import os
from pathlib import Path

from dataclasses import dataclass

@dataclass
class Config:
    GameDataPath: str
    GameDataRepo: str

    def load_from_disk(self):
        # 按照以下路径顺序寻找config.json文件
        # 1. 当前工作目录
        # 2. resources子目录
        # 3. data子目录
        # 未发现则抛出异常
        possible_paths = [
            Path.cwd() / 'config.json',
            Path.cwd() / 'resources' / 'config.json',
            Path.cwd() / 'data' / 'config.json'
        ]
        for path in possible_paths:
            if path.exists():
                with open(path, 'r') as f:
                    config = json.load(f)
                    self.GameDataPath = config.get('GameDataPath', '')
                    self.GameDataRepo = config.get('GameDataRepo', '')
                    return

    def load_from_astrbot_config(self,astr_config):

        if not isinstance(astr_config, dict):
            return

        # 逐项拷贝(需要判断是否有key)
        self.GameDataRepo = astr_config.get('GameDataRepo', self.GameDataPath)
        
        # 获取当前插件目录的绝对路径
        PLUGIN_DIR = Path(__file__).parent.absolute()
        PLUGIN_DATA_DIR = (PLUGIN_DIR / ".." / ".." / "amiyabot_resources").resolve()
        # GameDataPath 是下面的ArknightsGameData文件夹
        self.GameDataPath = str(PLUGIN_DATA_DIR / "ArknightsGameData")
        return
        
config = Config()


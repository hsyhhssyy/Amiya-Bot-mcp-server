# src/config/model.py
import json
import os
from pathlib import Path

from dataclasses import dataclass
from typing import Optional

FILE_PATH = Path(__file__).parent.parent.parent.resolve()

@dataclass
class Config:
    ProjectRoot: Optional[Path] = None
    ResourcePath: Optional[Path] = None
    GameDataRepo: Optional[str] = None

    def load_from_disk(self):
        # 按照以下路径顺序寻找config.json文件
        # 1. 当前工作目录
        # 2. resources子目录
        # 3. data子目录
        # 未发现则抛出异常
        possible_paths = [
            FILE_PATH / 'config.json',
            FILE_PATH / 'resources' / 'config.json',
            FILE_PATH / 'data' / 'config.json'
        ]
        for path in possible_paths:
            if path.exists():
                with open(path, 'r') as f:
                    config = json.load(f)
                    
                    cfgResourcePath = config.get('ResourcePath', '')
                    if cfgResourcePath == '':
                        # 如果配置文件中没有指定 ResourcePath，则使用默认路径
                        self.ResourcePath = Path((FILE_PATH / 'resources').resolve())
                    else:
                        self.ResourcePath = Path(cfgResourcePath)

                    self.GameDataRepo = config.get('GameDataRepo', '')

                    return

    # def load_from_astrbot_config(self,astr_config):

    #     if not isinstance(astr_config, dict):
    #         return

    #     # 逐项拷贝(需要判断是否有key)
    #     self.GameDataRepo = astr_config.get('GameDataRepo', self.ResourcePath)
        
    #     # 获取当前插件目录的绝对路径
    #     PLUGIN_DIR = Path(__file__).parent.absolute()
    #     PLUGIN_DATA_DIR = (PLUGIN_DIR / ".." / ".." / ".." / ".." / "plugin_data" / "amiya_bot_mcp_server" ).resolve()
        
    #     # 官方的代码是
    #     # from astrbot.core.utils.astrbot_path import get_astrbot_data_path
    #     # plugin_data_path = get_astrbot_data_path() / "plugin_data" / self.name
    #     # 但是这里为了避免引用Astrbot内部代码，直接构造路径

    #     self.ResourcePath = str(PLUGIN_DATA_DIR)

    #     return
        
config = Config()


"""
应用配置模块

提供应用程序的全局配置管理，包括：
- 应用基础配置（名称、版本、数据目录）
- 修炼提醒配置

配置支持 YAML 文件的序列化与反序列化。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    """应用程序配置类

    使用 dataclass 方便配置的管理和默认值设置。
    配置支持从 YAML 文件加载和保存。
    使用单例模式，通过 get() 方法获取全局唯一实例。

    Attributes:
        APP_NAME: 应用名称
        VERSION: 应用版本号
        DATA_DIR: 数据存储根目录
        DB_PATH: SQLite 数据库文件路径
        LOG_PATH: 日志文件路径
        REVIEW_TIME: 每日修炼提醒时间
        REVIEW_INTERVALS: 修炼间隔天数列表（基于艾宾浩斯遗忘曲线）
    """
    _instance: Optional["AppConfig"] = None
    
    APP_NAME: str = "算法修习助手"
    VERSION: str = "0.1.0"
    DATA_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent / "data"
    DB_PATH: Path = DATA_DIR / "algomate.db"
    LOG_PATH: Path = DATA_DIR.parent / "logs" / "algomate.log"

    REVIEW_TIME: str = "09:00"
    REVIEW_INTERVALS: list = field(default_factory=lambda: [1, 3, 7, 14, 30, 60])

    def __post_init__(self):
        """初始化后置处理

        确保数据目录和日志目录存在，并从环境变量加载敏感配置。
        """
        import os
        
        try:
            from dotenv import load_dotenv
            env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass

        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get(cls, config_path: Optional[Path] = None) -> "AppConfig":
        """获取配置单例实例

        如果实例不存在，则创建并初始化；否则返回已存在的实例。
        这是获取配置的推荐方式。

        Args:
            config_path: 配置文件路径，默认为 ~/.algomate/config.yaml

        Returns:
            AppConfig 单例实例

        Example:
            >>> config = AppConfig.get()
            >>> print(config.APP_NAME)
            算法修习助手
        """
        if cls._instance is None:
            cls._instance = cls.load(config_path)
        return cls._instance

    @classmethod
    def reload(cls, config_path: Optional[Path] = None) -> "AppConfig":
        """重新加载配置，清除单例缓存

        当配置文件被修改后，调用此方法强制重新加载最新配置。

        Args:
            config_path: 配置文件路径，默认为 ~/.algomate/config.yaml

        Returns:
            重新加载后的 AppConfig 实例

        Example:
            >>> # 修改配置后重新加载
            >>> config = AppConfig.reload()
        """
        cls._instance = None
        return cls.get(config_path)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "AppConfig":
        """从 YAML 文件加载配置

        Args:
            config_path: 配置文件路径，默认为 ~/.algomate/config.yaml

        Returns:
            AppConfig 实例
        """
        try:
            from dotenv import load_dotenv
            env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass

        # 允许通过环境变量 ALGOMATE_DB_PATH 覆盖数据库路径（便于本地开发/测试）
        if "ALGOMATE_DB_PATH" in os.environ:
            return cls(DB_PATH=Path(os.environ["ALGOMATE_DB_PATH"]))
        if "ALGOMATE_DATA_DIR" in os.environ:
            return cls(DATA_DIR=Path(os.environ["ALGOMATE_DATA_DIR"]))

        if config_path is None:
            config_path = cls.DATA_DIR / "config.yaml"

        if config_path.exists():
            try:
                import yaml
                with open(config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                
                # 将字符串路径转回 Path 对象
                if 'DATA_DIR' in data and isinstance(data['DATA_DIR'], str):
                    data['DATA_DIR'] = Path(data['DATA_DIR'])
                if 'DB_PATH' in data and isinstance(data['DB_PATH'], str):
                    data['DB_PATH'] = Path(data['DB_PATH'])
                if 'LOG_PATH' in data and isinstance(data['LOG_PATH'], str):
                    data['LOG_PATH'] = Path(data['LOG_PATH'])
                
                return cls(**data)
            except ImportError:
                pass
        return cls()

    def save(self, config_path: Optional[Path] = None):
        """保存配置到 YAML 文件

        Args:
            config_path: 配置文件路径，默认为 ~/.algomate/config.yaml
        """
        import yaml
        if config_path is None:
            config_path = self.DATA_DIR / "config.yaml"

        # 只保存可序列化的字段，排除Path类型和单例实例
        save_data = {}
        for key, value in self.__dict__.items():
            if key == '_instance':  # 排除单例实例字段
                continue
            if isinstance(value, Path):  # Path对象转为字符串
                save_data[key] = str(value)
            else:
                save_data[key] = value

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(save_data, f, allow_unicode=True, default_flow_style=False)

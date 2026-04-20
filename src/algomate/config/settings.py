"""
应用配置模块

提供应用程序的全局配置管理，包括：
- 应用基础配置（名称、版本、数据目录）
- AI模型配置（智谱GLM API）
- 邮件服务配置（SMTP）
- 复习提醒配置

配置支持 YAML 文件的序列化与反序列化。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    """应用程序配置类

    使用 dataclass 方便配置的管理和默认值设置。
    配置支持从 YAML 文件加载和保存。

    Attributes:
        APP_NAME: 应用名称
        VERSION: 应用版本号
        DATA_DIR: 数据存储根目录
        DB_PATH: SQLite 数据库文件路径
        LOG_PATH: 日志文件路径
        LLM_API_KEY: 大模型 API密钥
        LLM_MODEL: 大模型名称
        LLM_BASE_URL: 大模型 API 地址
        SMTP_HOST: SMTP 服务器地址
        SMTP_PORT: SMTP 服务器端口
        SMTP_USER: SMTP 用户名
        SMTP_PASSWORD: SMTP 密码
        SMTP_USE_TLS: 是否使用 TLS 加密
        EMAIL_FROM: 发件人邮箱
        EMAIL_TO: 收件人邮箱
        REVIEW_TIME: 每日复习提醒时间
        REVIEW_ENABLED: 是否启用复习提醒
        REVIEW_INTERVALS: 复习间隔天数列表（基于艾宾浩斯遗忘曲线）
    """
    APP_NAME: str = "算法学习助手"
    VERSION: str = "0.1.0"
    DATA_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent / "data"
    DB_PATH: Path = DATA_DIR / "algomate.db"
    LOG_PATH: Path = DATA_DIR.parent / "logs" / "algomate.log"

    LLM_API_KEY: str = ""
    LLM_MODEL: str = "glm-4"
    LLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"

    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = ""
    EMAIL_TO: str = ""

    REVIEW_TIME: str = "09:00"
    REVIEW_ENABLED: bool = True
    REVIEW_INTERVALS: list = field(default_factory=lambda: [1, 3, 7, 14, 30, 60])

    def __post_init__(self):
        """初始化后置处理

        确保数据目录和日志目录存在，并从环境变量加载敏感配置。
        """
        import os
        from dotenv import load_dotenv

        env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        if not self.LLM_API_KEY:
            self.LLM_API_KEY = os.getenv("LLM_API_KEY", "")
        if not self.SMTP_PASSWORD:
            self.SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
        if not self.SMTP_USER:
            self.SMTP_USER = os.getenv("SMTP_USER", "")
        if not self.EMAIL_FROM:
            self.EMAIL_FROM = os.getenv("EMAIL_FROM", "")
        if not self.EMAIL_TO:
            self.EMAIL_TO = os.getenv("EMAIL_TO", "")

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "AppConfig":
        """从 YAML 文件加载配置

        Args:
            config_path: 配置文件路径，默认为 ~/.algomate/config.yaml

        Returns:
            AppConfig 实例
        """
        import yaml
        from dotenv import load_dotenv

        env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        if config_path is None:
            config_path = cls.DATA_DIR / "config.yaml"

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()

    def save(self, config_path: Optional[Path] = None):
        """保存配置到 YAML 文件

        Args:
            config_path: 配置文件路径，默认为 ~/.algomate/config.yaml
        """
        import yaml
        if config_path is None:
            config_path = self.DATA_DIR / "config.yaml"

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.__dict__, f, allow_unicode=True, default_flow_style=False)

from pathlib import Path
from typing import Optional, Union, TYPE_CHECKING
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

if TYPE_CHECKING:
    from algomate.config.settings import AppConfig

Base = declarative_base()


def init_db(config: Optional["AppConfig"] = None) -> "Database":
    """初始化数据库

    创建数据库连接并初始化所有表结构。
    这是初始化数据库的推荐方式。

    Args:
        config: 应用配置，默认从配置文件加载

    Returns:
        Database 实例

    Example:
        >>> from algomate.config.settings import AppConfig
        >>> from algomate.data.database import init_db
        >>> config = AppConfig.get()
        >>> db = init_db(config)
        >>> session = db.get_session()
    """
    return Database.get_instance(config)


class Database:
    """数据库管理类

    使用单例模式管理数据库连接，确保整个应用共享同一个数据库连接池。
    使用 SQLite 作为数据库，通过 SQLAlchemy ORM 进行数据库操作。

    Attributes:
        _instance: 单例实例
        engine: SQLAlchemy 引擎
        SessionLocal: Session 工厂类，用于创建数据库会话

    Example:
        db = Database.get_instance()
        session = db.get_session()
        # 使用 session 进行数据库操作
        session.close()
    """
    _instance: Optional["Database"] = None

    def __init__(self, db_path: Union[str, Path]):
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        from . import models
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    @classmethod
    def get_instance(cls, config: Optional["AppConfig"] = None) -> "Database":
        if cls._instance is None:
            if config is None:
                from algomate.config.settings import AppConfig
                config = AppConfig.load()
            cls._instance = cls(config.DB_PATH)
        return cls._instance

    def get_session(self) -> Session:
        return self.SessionLocal()

    def close(self):
        """关闭数据库连接并重置单例

        通常在应用退出时调用，用于释放资源。
        """
        if self._instance:
            self._instance.engine.dispose()
            Database._instance = None

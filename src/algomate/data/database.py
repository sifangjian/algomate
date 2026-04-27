from pathlib import Path
from typing import Optional, Union, TYPE_CHECKING
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

if TYPE_CHECKING:
    from algomate.config.settings import AppConfig

Base = declarative_base()

_models_imported = False


def _ensure_models_imported():
    """确保模型只被导入一次"""
    global _models_imported
    if not _models_imported:
        from algomate.models import (
            Note, Card, NPC, Boss, Question, AnswerRecord,
            DialogueRecord, ReviewRecord, LearningProgress, UserSetting
        )
        _models_imported = True


def _auto_migrate(db_path: Union[str, Path]):
    """自动迁移数据库表结构，添加缺失的列"""
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    inspector = inspect(engine)

    for table_name in Base.metadata.tables:
        columns = inspector.get_columns(table_name)
        existing_columns = {col['name'] for col in columns}

        table = Base.metadata.tables[table_name]
        for column in table.columns:
            if column.name not in existing_columns:
                try:
                    col_type = column.type.compile(engine.dialect)
                    default_value = column.default.arg if column.default else 'NULL'
                    nullable = 'NOT NULL' if not column.nullable else 'NULL'

                    alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable}"
                    if default_value != 'NULL' and default_value is not None:
                        if isinstance(default_value, str):
                            alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable} DEFAULT '{default_value}'"
                        else:
                            alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable} DEFAULT {default_value}"

                    with engine.connect() as conn:
                        conn.execute(text(alter_stmt))
                        conn.commit()
                    print(f"  [MIGRATION] Added column {column.name} to table {table_name}")
                except Exception as e:
                    print(f"  [MIGRATION] Could not add column {column.name}: {e}")

    engine.dispose()


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
        _ensure_models_imported()
        _auto_migrate(db_path)
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
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

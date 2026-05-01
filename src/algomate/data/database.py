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
        try:
            columns = inspector.get_columns(table_name)
        except Exception:
            continue
        existing_columns = {col['name'] for col in columns}

        table = Base.metadata.tables[table_name]
        for column in table.columns:
            if column.name not in existing_columns:
                try:
                    col_type = column.type.compile(engine.dialect)

                    default_value = 'NULL'
                    if column.default is not None:
                        if callable(column.default.arg):
                            default_value = 'NULL'
                        else:
                            default_value = column.default.arg

                    if column.server_default is not None:
                        default_value = 'NULL'

                    nullable = 'NOT NULL' if not column.nullable else 'NULL'

                    if nullable == 'NOT NULL' and default_value == 'NULL':
                        nullable = 'NULL'

                    alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable}"
                    if default_value != 'NULL' and default_value is not None:
                        if isinstance(default_value, str):
                            escaped = default_value.replace("'", "''")
                            alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable} DEFAULT '{escaped}'"
                        elif isinstance(default_value, bool):
                            alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable} DEFAULT {1 if default_value else 0}"
                        elif isinstance(default_value, (int, float)):
                            alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable} DEFAULT {default_value}"
                        else:
                            nullable = 'NULL'
                            alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable}"

                    with engine.connect() as conn:
                        conn.execute(text(alter_stmt))
                        conn.commit()
                    print(f"  [MIGRATION] Added column {column.name} to table {table_name}")
                except Exception as e:
                    print(f"  [MIGRATION] Could not add column {column.name}: {e}")

    _fix_orphan_notnull_columns(engine)

    engine.dispose()


def _fix_orphan_notnull_columns(engine):
    inspector = inspect(engine)

    for table_name in Base.metadata.tables:
        try:
            db_columns = inspector.get_columns(table_name)
        except Exception:
            continue

        model_column_names = {col.name for col in Base.metadata.tables[table_name].columns}

        orphan_notnull = set()
        for col in db_columns:
            if col['name'] not in model_column_names and not col.get('nullable', True):
                orphan_notnull.add(col['name'])

        if not orphan_notnull:
            continue

        pk_constraint = inspector.get_pk_constraint(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)

        pk_columns = pk_constraint.get('constrained_columns', [])

        has_autoincrement = False
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:tname"),
                {"tname": table_name}
            )
            row = result.fetchone()
            if row and row[0] and 'AUTOINCREMENT' in row[0].upper():
                has_autoincrement = True

        col_defs = []
        for col in db_columns:
            parts = []
            col_name = col['name']
            col_type = str(col['type'])

            parts.append(f'"{col_name}"')
            parts.append(col_type)

            is_pk = col_name in pk_columns and len(pk_columns) == 1

            if is_pk:
                parts.append('PRIMARY KEY')
                if has_autoincrement and col_type.upper() == 'INTEGER':
                    parts.append('AUTOINCREMENT')
            elif col_name not in orphan_notnull and not col.get('nullable', True):
                parts.append('NOT NULL')

            default = col.get('default')
            if default is not None:
                if isinstance(default, (int, float)):
                    parts.append(f'DEFAULT {default}')
                elif isinstance(default, str):
                    parts.append(f'DEFAULT {default}')
                else:
                    parts.append(f'DEFAULT {default}')

            col_defs.append(' '.join(parts))

        if len(pk_columns) > 1:
            pk_str = ', '.join(f'"{c}"' for c in pk_columns)
            col_defs.append(f'PRIMARY KEY ({pk_str})')

        for fk in foreign_keys:
            constrained = ', '.join(f'"{c}"' for c in fk['constrained_columns'])
            referred_table = fk['referred_table']
            referred = ', '.join(f'"{c}"' for c in fk['referred_columns'])
            col_defs.append(f'FOREIGN KEY ({constrained}) REFERENCES "{referred_table}" ({referred})')

        try:
            unique_constraints = inspector.get_unique_constraints(table_name)
            for uc in unique_constraints:
                uc_cols = ', '.join(f'"{c}"' for c in uc['column_names'])
                col_defs.append(f'UNIQUE ({uc_cols})')
        except Exception:
            pass

        temp_name = f'_temp_{table_name}'
        create_sql = f'CREATE TABLE "{temp_name}" (\n    ' + ',\n    '.join(col_defs) + '\n)'

        with engine.connect() as conn:
            conn.execute(text(create_sql))

            col_names = [col['name'] for col in db_columns]
            cols = ', '.join(f'"{c}"' for c in col_names)
            conn.execute(text(f'INSERT INTO "{temp_name}" ({cols}) SELECT {cols} FROM "{table_name}"'))
            conn.execute(text(f'DROP TABLE "{table_name}"'))
            conn.execute(text(f'ALTER TABLE "{temp_name}" RENAME TO "{table_name}"'))

            for idx in indexes:
                if idx['name'].startswith('sqlite_autoindex_'):
                    continue
                unique = 'UNIQUE ' if idx.get('unique', False) else ''
                idx_cols = ', '.join(f'"{c}"' for c in idx['column_names'])
                conn.execute(text(f'CREATE {unique}INDEX "{idx["name"]}" ON "{table_name}" ({idx_cols})'))

            conn.commit()

        for col_name in orphan_notnull:
            print(f"  [MIGRATION] Made orphan column {col_name} in table {table_name} nullable")


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

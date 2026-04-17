"""
数据模型模块

定义应用程序的数据库模型，包括：
- Note: 笔记模型
- ReviewRecord: 复习记录模型
- Question: 题目模型
- AnswerRecord: 答题记录模型
- LearningProgress: 学习进度模型
- UserSetting: 用户设置模型

使用 SQLAlchemy ORM 框架进行数据库操作。
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.pool import StaticPool
from pathlib import Path


Base = declarative_base()


class Note(Base):
    """笔记模型

    存储用户的算法学习笔记，包含笔记内容、分类信息、掌握程度等。

    Attributes:
        id: 笔记唯一标识
        title: 笔记标题
        content: 笔记内容（Markdown格式）
        summary: AI提取的笔记摘要
        algorithm_type: 算法类型
        tags: 标签列表（JSON格式）
        difficulty: 难度等级
        mastery_level: 掌握程度（0-100）
        review_count: 已复习次数
        created_at: 创建时间
        updated_at: 更新时间
        last_reviewed: 最近复习时间
        next_review_date: 下次复习日期
        questions: 关联的题目列表
        review_records: 关联的复习记录列表
    """
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, default="")
    algorithm_type = Column(String(50), default="其他")
    tags = Column(Text, default="[]")
    difficulty = Column(String(10), default="中等")
    mastery_level = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_reviewed = Column(DateTime, nullable=True)
    next_review_date = Column(Date, nullable=True)

    questions: List["Question"] = relationship("Question", back_populates="note")
    review_records: List["ReviewRecord"] = relationship("ReviewRecord", back_populates="note")


class ReviewRecord(Base):
    """复习记录模型

    记录用户的复习活动，用于追踪复习历史和效果。

    Attributes:
        id: 记录唯一标识
        note_id: 关联笔记ID
        review_date: 复习日期
        status: 复习状态（pending/completed/skipped）
        score: 本次复习得分
        note: 关联的笔记对象
    """
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    review_date = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="pending")
    score = Column(Integer, nullable=True)

    note: "Note" = relationship("Note", back_populates="review_records")


class Question(Base):
    """题目模型

    存储与笔记关联的练习题目，支持多种题型。

    Attributes:
        id: 题目唯一标识
        note_id: 关联笔记ID
        question_type: 题目类型（选择题/简答题/代码题）
        content: 题目内容
        answer: 参考答案
        explanation: 题目解析
        created_at: 创建时间
        note: 关联的笔记对象
        answer_records: 关联的答题记录列表
    """
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    question_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    answer = Column(Text, default="")
    explanation = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    note: "Note" = relationship("Note", back_populates="questions")
    answer_records: List["AnswerRecord"] = relationship("AnswerRecord", back_populates="question")


class AnswerRecord(Base):
    """答题记录模型

    记录用户的答题历史和反馈信息。

    Attributes:
        id: 记录唯一标识
        question_id: 关联题目ID
        user_answer: 用户答案
        is_correct: 是否正确
        feedback: AI反馈信息
        answered_at: 答题时间
        question: 关联的题目对象
    """
    __tablename__ = "answer_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    feedback = Column(Text, default="")
    answered_at = Column(DateTime, default=datetime.now)

    question: "Question" = relationship("Question", back_populates="answer_records")


class LearningProgress(Base):
    """学习进度模型

    记录用户每日的学习统计数据。

    Attributes:
        id: 记录唯一标识
        date: 日期（唯一）
        notes_count: 当日新增笔记数
        review_count: 当日复习题目数
        correct_count: 当日正确答题数
        total_count: 当日总答题数
    """
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    notes_count = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)


class UserSetting(Base):
    """用户设置模型

    存储用户的个性化设置项。

    Attributes:
        id: 设置项唯一标识
        key: 设置项名称（唯一）
        value: 设置值
        updated_at: 更新时间
    """
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Database:
    """数据库管理类

    实现单例模式的数据库连接管理器。

    使用 SQLite 数据库，通过 SQLAlchemy ORM 进行操作。
    使用 StaticPool 实现单例连接，确保线程安全。

    Attributes:
        _instance: 单例实例
        engine: SQLAlchemy 引擎
        SessionLocal: Session 工厂类

    Example:
        db = Database.get_instance()
        session = db.get_session()
        # 使用 session 进行数据库操作
        session.close()
    """
    _instance: Optional["Database"] = None

    def __init__(self, db_path: Path):
        """初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    @classmethod
    def get_instance(cls, config: Optional[AppConfig] = None) -> "Database":
        """获取数据库单例实例

        Args:
            config: 应用配置，用于获取数据库路径

        Returns:
            Database 单例实例
        """
        if cls._instance is None:
            if config is None:
                from ..config.settings import AppConfig
                config = AppConfig.load()
            cls._instance = cls(config.DB_PATH)
        return cls._instance

    def get_session(self):
        """获取新的数据库会话

        Returns:
            SQLAlchemy Session 实例
        """
        return self.SessionLocal()

    def close(self):
        """关闭数据库连接并重置单例"""
        if self._instance:
            self._instance.engine.dispose()
            Database._instance = None

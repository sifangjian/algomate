"""
答题记录仓库模块

提供答题记录数据的数据库操作，包括记录的创建、查询等功能。
"""

from typing import List, Optional
from datetime import datetime, timedelta
from ..models import AnswerRecord
from ..database import Database


class AnswerRecordRepository:
    """答题记录数据仓库

    负责答题记录数据的数据库操作。

    Attributes:
        db: 数据库实例
    """

    def __init__(self, db: Database):
        """初始化答题记录仓库

        Args:
            db: 数据库实例
        """
        self.db = db

    def create(
        self, question_id: int, user_answer: str, is_correct: bool, **kwargs
    ) -> AnswerRecord:
        """创建答题记录

        Args:
            question_id: 题目ID
            user_answer: 用户答案
            is_correct: 是否正确
            **kwargs: 其他可选参数

        Returns:
            创建的答题记录对象
        """
        session = self.db.get_session()
        try:
            record = AnswerRecord(
                question_id=question_id,
                user_answer=user_answer,
                is_correct=is_correct,
                **kwargs
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()

    def get_by_id(self, record_id: int) -> Optional[AnswerRecord]:
        """根据ID获取答题记录

        Args:
            record_id: 记录ID

        Returns:
            答题记录对象，若不存在则返回 None
        """
        session = self.db.get_session()
        try:
            return session.query(AnswerRecord).filter(AnswerRecord.id == record_id).first()
        finally:
            session.close()

    def get_recent_records(self, days: int = 30) -> List[AnswerRecord]:
        """获取近期的答题记录

        Args:
            days: 天数，默认30天

        Returns:
            答题记录列表
        """
        session = self.db.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            return (
                session.query(AnswerRecord)
                .filter(AnswerRecord.answered_at >= cutoff_date)
                .all()
            )
        finally:
            session.close()

    def get_by_question_id(self, question_id: int) -> List[AnswerRecord]:
        """获取指定题目的所有答题记录

        Args:
            question_id: 题目ID

        Returns:
            答题记录列表
        """
        session = self.db.get_session()
        try:
            return (
                session.query(AnswerRecord)
                .filter(AnswerRecord.question_id == question_id)
                .order_by(AnswerRecord.answered_at.desc())
                .all()
            )
        finally:
            session.close()

    def get_all(self) -> List[AnswerRecord]:
        """获取所有答题记录

        按答题时间倒序返回。

        Returns:
            答题记录列表
        """
        session = self.db.get_session()
        try:
            return session.query(AnswerRecord).order_by(AnswerRecord.answered_at.desc()).all()
        finally:
            session.close()

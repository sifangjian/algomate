"""
试炼仓库模块

提供试炼数据的数据库操作，包括增删改查等功能。
"""

from typing import List, Optional
from datetime import datetime
from algomate.models import Question
from ..database import Database


class QuestionRepository:
    """试炼数据仓库

    负责试炼数据的数据库操作。

    Attributes:
        db: 数据库实例
    """

    def __init__(self, db: Database):
        """初始化试炼仓库

        Args:
            db: 数据库实例
        """
        self.db = db

    def create(self, card_id: int, question_type: str, content: str, **kwargs) -> Question:
        """创建新试炼

        Args:
            card_id: 关联卡牌ID
            question_type: 试炼类型
            content: 试炼内容
            **kwargs: 其他可选参数

        Returns:
            创建的试炼对象
        """
        session = self.db.get_session()
        try:
            question = Question(
                card_id=card_id,
                question_type=question_type,
                content=content,
                **kwargs
            )
            session.add(question)
            session.commit()
            session.refresh(question)
            return question
        finally:
            session.close()

    def get_by_id(self, question_id: int) -> Optional[Question]:
        """根据ID获取试炼

        Args:
            question_id: 试炼ID

        Returns:
            试炼对象，若不存在则返回 None
        """
        session = self.db.get_session()
        try:
            return session.query(Question).filter(Question.id == question_id).first()
        finally:
            session.close()

    def get_by_card_id(self, card_id: int) -> List[Question]:
        """获取指定卡牌的所有试炼

        Args:
            card_id: 卡牌ID

        Returns:
            试炼列表
        """
        session = self.db.get_session()
        try:
            return session.query(Question).filter(Question.card_id == card_id).all()
        finally:
            session.close()

    def get_all(self) -> List[Question]:
        """获取所有试炼

        按创建时间倒序返回。

        Returns:
            试炼列表
        """
        session = self.db.get_session()
        try:
            return session.query(Question).order_by(Question.created_at.desc()).all()
        finally:
            session.close()

    def delete(self, question_id: int) -> bool:
        """删除试炼

        Args:
            question_id: 试炼ID

        Returns:
            删除是否成功
        """
        session = self.db.get_session()
        try:
            question = session.query(Question).filter(Question.id == question_id).first()
            if question:
                session.delete(question)
                session.commit()
                return True
            return False
        finally:
            session.close()

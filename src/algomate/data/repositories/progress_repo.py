"""
学习进度仓库模块

提供学习进度数据的数据库操作，包括进度的创建、更新、查询等功能。
"""

from typing import List, Optional
from datetime import date
from ..models import LearningProgress, Database


class ProgressRepository:
    """学习进度数据仓库

    负责学习进度数据的数据库操作。

    Attributes:
        db: 数据库实例
    """

    def __init__(self, db: Database):
        """初始化学习进度仓库

        Args:
            db: 数据库实例
        """
        self.db = db

    def create_or_update(self, target_date: date, **kwargs) -> LearningProgress:
        """创建或更新当日学习进度

        如果当日已有进度记录，则累加各项数值。

        Args:
            target_date: 目标日期
            **kwargs: 可选参数（notes_count, review_count, correct_count, total_count）

        Returns:
            学习进度对象
        """
        session = self.db.get_session()
        try:
            progress = session.query(LearningProgress).filter(LearningProgress.date == target_date).first()
            if progress:
                for key, value in kwargs.items():
                    if value:
                        setattr(progress, key, getattr(progress, key, 0) + value)
            else:
                progress = LearningProgress(date=target_date, **kwargs)
                session.add(progress)
            session.commit()
            session.refresh(progress)
            return progress
        finally:
            session.close()

    def get_by_date(self, target_date: date) -> Optional[LearningProgress]:
        """获取指定日期的学习进度

        Args:
            target_date: 目标日期

        Returns:
            学习进度对象，若不存在则返回 None
        """
        session = self.db.get_session()
        try:
            return session.query(LearningProgress).filter(LearningProgress.date == target_date).first()
        finally:
            session.close()

    def get_date_range(self, start_date: date, end_date: date) -> List[LearningProgress]:
        """获取日期范围内的学习进度

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            学习进度列表
        """
        session = self.db.get_session()
        try:
            return (
                session.query(LearningProgress)
                .filter(LearningProgress.date >= start_date, LearningProgress.date <= end_date)
                .order_by(LearningProgress.date)
                .all()
            )
        finally:
            session.close()

    def get_all(self) -> List[LearningProgress]:
        """获取所有学习进度记录

        按日期倒序返回。

        Returns:
            学习进度列表
        """
        session = self.db.get_session()
        try:
            return session.query(LearningProgress).order_by(LearningProgress.date.desc()).all()
        finally:
            session.close()

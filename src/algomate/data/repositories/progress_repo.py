"""
修为仓库模块

提供修为数据的数据库操作，包括进度的创建、更新、查询等功能。
"""

from typing import List, Optional
from datetime import date
from algomate.models import LearningProgress
from ..database import Database


class ProgressRepository:
    """修为数据仓库

    负责修为数据的数据库操作。

    Attributes:
        db: 数据库实例
    """

    def __init__(self, db: Database):
        """初始化修为仓库

        Args:
            db: 数据库实例
        """
        self.db = db

    def create_or_update(self, target_date: date, **kwargs) -> LearningProgress:
        """创建或更新当日修为

        如果当日已有进度记录，则累加各项数值。

        Args:
            target_date: 目标日期
            **kwargs: 可选参数（notes_count, review_count, correct_count, total_count）

        Returns:
            修为对象
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
        """获取指定日期的修为

        Args:
            target_date: 目标日期

        Returns:
            修为对象，若不存在则返回 None
        """
        session = self.db.get_session()
        try:
            return session.query(LearningProgress).filter(LearningProgress.date == target_date).first()
        finally:
            session.close()

    def get_date_range(self, start_date: date, end_date: date) -> List[LearningProgress]:
        """获取日期范围内的修为

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            修为列表
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
        """获取所有修为记录

        按日期倒序返回。

        Returns:
            修为列表
        """
        session = self.db.get_session()
        try:
            return session.query(LearningProgress).order_by(LearningProgress.date.desc()).all()
        finally:
            session.close()

    def get_consecutive_days(self) -> int:
        """计算连续修习天数

        从今天开始往前逐日检查，如果某天存在 learning_progress 记录且
        review_count > 0 或 notes_count > 0，则计入连续天数。
        遇到第一个无记录或记录为零的天即停止计数。
        今天没有记录时，从昨天开始计算。

        Returns:
            连续修习天数
        """
        from datetime import timedelta

        session = self.db.get_session()
        try:
            today = date.today()
            check_date = today
            first_record = session.query(LearningProgress).filter(
                LearningProgress.date == today
            ).first()

            if not first_record or (first_record.review_count == 0 and first_record.notes_count == 0):
                check_date = today - timedelta(days=1)

            consecutive = 0
            current = check_date
            while True:
                record = session.query(LearningProgress).filter(
                    LearningProgress.date == current
                ).first()
                if record and (record.review_count > 0 or record.notes_count > 0):
                    consecutive += 1
                    current -= timedelta(days=1)
                else:
                    break
            return consecutive
        finally:
            session.close()

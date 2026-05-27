"""
修炼记录仓库模块

提供修炼记录数据的数据库操作，包括记录的创建、状态更新等功能。
"""

from typing import List, Optional
from datetime import datetime
from algomate.models import ReviewRecord
from ..database import Database


class ReviewRecordRepository:
    """修炼记录数据仓库

    负责修炼记录数据的数据库操作。

    Attributes:
        db: 数据库实例
    """

    def __init__(self, db: Database):
        self.db = db

    def create(self, card_id: int, review_date: datetime, **kwargs) -> ReviewRecord:
        """创建修炼记录

        Args:
            card_id: 关联卡牌ID
            review_date: 修炼日期
            **kwargs: 其他可选参数

        Returns:
            创建的修炼记录对象
        """
        session = self.db.get_session()
        try:
            record = ReviewRecord(
                card_id=card_id,
                review_date=review_date,
                **kwargs
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()

    def get_by_id(self, record_id: int) -> Optional[ReviewRecord]:
        """根据ID获取修炼记录

        Args:
            record_id: 记录ID

        Returns:
            修炼记录对象，若不存在则返回 None
        """
        session = self.db.get_session()
        try:
            return session.query(ReviewRecord).filter(ReviewRecord.id == record_id).first()
        finally:
            session.close()

    def get_by_card_id(self, card_id: int) -> List[ReviewRecord]:
        """获取指定卡牌的所有修炼记录

        Args:
            card_id: 卡牌ID

        Returns:
            修炼记录列表
        """
        session = self.db.get_session()
        try:
            return (
                session.query(ReviewRecord)
                .filter(ReviewRecord.card_id == card_id)
                .order_by(ReviewRecord.review_date.desc())
                .all()
            )
        finally:
            session.close()

    def get_pending_reviews(self) -> List[ReviewRecord]:
        """获取待完成的修炼记录

        Returns:
            状态为 pending 的修炼记录列表
        """
        session = self.db.get_session()
        try:
            return (
                session.query(ReviewRecord)
                .filter(ReviewRecord.status == "pending")
                .order_by(ReviewRecord.review_date)
                .all()
            )
        finally:
            session.close()

    def update_status(self, record_id: int, status: str, score: int = None) -> Optional[ReviewRecord]:
        """更新修炼记录状态

        Args:
            record_id: 记录ID
            status: 新状态
            score: 可选的战绩

        Returns:
            更新后的修炼记录对象
        """
        session = self.db.get_session()
        try:
            record = session.query(ReviewRecord).filter(ReviewRecord.id == record_id).first()
            if record:
                record.status = status
                if score is not None:
                    record.score = score
                session.commit()
                session.refresh(record)
            return record
        finally:
            session.close()

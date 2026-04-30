"""
心得仓库模块

.. deprecated::
    此模块已废弃。心得(Note)模型已迁移到卡牌(Card)模型。
    请使用 card_repo.CardRepository 替代。

提供心得数据的数据库操作，包括增删改查等基础功能，
以及按算法类型查询、获取待修炼心得等业务功能。
"""

from typing import List, Optional
from datetime import datetime, date
from algomate.models import Note
from ..database import Database


class NoteRepository:
    """心得数据仓库

    .. deprecated:: 此类已废弃。请使用 card_repo.CardRepository 替代。

    负责心得数据的数据库操作，实现数据访问层职责。

    Attributes:
        db: 数据库实例
    """

    def __init__(self, db: Database):
        """初始化心得仓库

        Args:
            db: 数据库实例
        """
        self.db = db

    def create(self, title: str, content: str, **kwargs) -> Note:
        """创建新心得

        Args:
            title: 心得标题
            content: 心得内容
            **kwargs: 其他可选参数

        Returns:
            创建的心得对象
        """
        session = self.db.get_session()
        try:
            note = Note(title=title, content=content, **kwargs)
            session.add(note)
            session.commit()
            session.refresh(note)
            return note
        finally:
            session.close()

    def get_by_id(self, note_id: int) -> Optional[Note]:
        """根据ID获取心得

        Args:
            note_id: 心得ID

        Returns:
            心得对象，若不存在则返回 None
        """
        session = self.db.get_session()
        try:
            return session.query(Note).filter(Note.id == note_id).first()
        finally:
            session.close()

    def get_all(self) -> List[Note]:
        """获取所有心得

        按创建时间倒序返回。

        Returns:
            心得列表
        """
        session = self.db.get_session()
        try:
            return session.query(Note).order_by(Note.created_at.desc()).all()
        finally:
            session.close()

    def update(self, note: Note) -> Note:
        """更新心得

        Args:
            note: 心得对象

        Returns:
            更新后的心得对象
        """
        session = self.db.get_session()
        try:
            note.updated_at = datetime.now()
            session.commit()
            session.refresh(note)
            return note
        finally:
            session.close()

    def delete(self, note_id: int) -> bool:
        """删除心得

        Args:
            note_id: 心得ID

        Returns:
            删除是否成功
        """
        session = self.db.get_session()
        try:
            note = session.query(Note).filter(Note.id == note_id).first()
            if note:
                session.delete(note)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_notes_due_for_review(self, end_date: date) -> List[Note]:
        """获取待修炼的心得

        Args:
            end_date: 截止日期

        Returns:
            符合修炼条件的心得列表
        """
        session = self.db.get_session()
        try:
            return (
                session.query(Note)
                .filter(Note.next_review_date <= end_date)
                .order_by(Note.next_review_date)
                .all()
            )
        finally:
            session.close()

    def get_by_algorithm_type(self, algo_type: str) -> List[Note]:
        """按算法类型获取心得

        Args:
            algo_type: 算法类型

        Returns:
            指定类型的心得列表
        """
        session = self.db.get_session()
        try:
            return (
                session.query(Note)
                .filter(Note.algorithm_type == algo_type)
                .order_by(Note.created_at.desc())
                .all()
            )
        finally:
            session.close()

    def get_weak_notes(self, threshold: int = 50) -> List[Note]:
        """获取薄弱心得

        Args:
            threshold: 领悟程度阈值，默认50

        Returns:
            领悟程度低于阈值的心得列表
        """
        session = self.db.get_session()
        try:
            return (
                session.query(Note)
                .filter(Note.mastery_level < threshold)
                .order_by(Note.mastery_level)
                .all()
            )
        finally:
            session.close()

    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Note]:
        """搜索心得

        根据关键词搜索心得，支持算法类型、标题、内容搜索。

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            匹配的心得列表
        """
        session = self.db.get_session()
        try:
            pattern = f"%{keyword}%"
            return (
                session.query(Note)
                .filter(
                    Note.algorithm_type.like(pattern) |
                    Note.title.like(pattern) |
                    Note.content.like(pattern) |
                    Note.tags.like(pattern)
                )
                .order_by(Note.updated_at.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    def get_notes_due_for_review(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days_ahead: Optional[int] = None,
    ) -> List[Note]:
        """获取待修炼的心得

        .. deprecated:: 此方法已废弃。修炼追踪已统一到 Card 模型，请使用 CardRepository 替代。

        Args:
            start_date: 开始日期（可选）
            end_date: 截止日期（可选）
            days_ahead: 未来天数（可选，与 end_date 互斥）

        Returns:
            符合修炼条件的心得列表
        """
        session = self.db.get_session()
        try:
            query = session.query(Note)

            if days_ahead is not None:
                from datetime import timedelta
                end = date.today() + timedelta(days=days_ahead)
                query = query.filter(Note.next_review_date <= end)
            elif end_date is not None:
                query = query.filter(Note.next_review_date <= end_date)

            if start_date is not None:
                query = query.filter(Note.next_review_date >= start_date)

            return query.order_by(Note.next_review_date).all()
        finally:
            session.close()

"""
复习计划服务模块

提供今日复习计划相关的业务逻辑：
- 获取今日应复习的笔记列表
- 生成和管理复习记录
- 更新复习状态和掌握程度
- 获取薄弱点提醒
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from ..data.database import Database
from ..data.repositories.note_repo import NoteRepository
from ..data.repositories.review_repo import ReviewRecordRepository
from ..data.models import Note, ReviewRecord
from ..core.memory.forgotten_curve import ForgottenCurve


class ReviewPlanService:
    """复习计划服务

    负责管理今日复习计划的业务逻辑，包括：
    - 获取今日应复习的笔记
    - 创建复习记录
    - 完成复习后更新掌握程度
    - 识别薄弱点

    Attributes:
        db: 数据库实例
        note_repo: 笔记仓库
        review_repo: 复习记录仓库
        forgotten_curve: 遗忘曲线算法
    """

    def __init__(self, db: Database = None):
        """初始化复习计划服务

        Args:
            db: 数据库实例，默认使用单例
        """
        self.db = db or Database.get_instance()
        self.note_repo = NoteRepository(self.db)
        self.review_repo = ReviewRecordRepository(self.db)
        self.forgotten_curve = ForgottenCurve()

    def get_today_review_plan(self, target_date: date = None) -> List[Dict[str, Any]]:
        """获取今日复习计划

        获取指定日期应复习的笔记列表，包含笔记信息和复习状态。

        Args:
            target_date: 目标日期，默认为今天

        Returns:
            复习计划列表，每项包含笔记信息和复习状态
        """
        if target_date is None:
            target_date = date.today()

        session = self.db.get_session()
        try:
            notes = (
                session.query(Note)
                .filter(Note.next_review_date <= target_date)
                .order_by(Note.next_review_date)
                .all()
            )

            review_plan = []
            for note in notes:
                pending_records = (
                    session.query(ReviewRecord)
                    .filter(
                        ReviewRecord.note_id == note.id,
                        ReviewRecord.status == "pending"
                    )
                    .order_by(ReviewRecord.review_date)
                    .all()
                )

                review_plan.append({
                    "note_id": note.id,
                    "title": note.title,
                    "summary": note.summary or "",
                    "algorithm_type": note.algorithm_type,
                    "difficulty": note.difficulty,
                    "mastery_level": note.mastery_level,
                    "review_count": note.review_count,
                    "last_reviewed": note.last_reviewed.isoformat() if note.last_reviewed else None,
                    "next_review_date": note.next_review_date.isoformat() if note.next_review_date else None,
                    "pending_records": [
                        {"id": r.id, "review_date": r.review_date.isoformat(), "status": r.status}
                        for r in pending_records
                    ],
                    "is_overdue": note.next_review_date < target_date if note.next_review_date else False
                })

            return review_plan
        finally:
            session.close()

    def get_weak_points(self, threshold: int = 70) -> List[Dict[str, Any]]:
        """获取薄弱点提醒

        获取掌握程度低于阈值的笔记，作为薄弱点提醒。

        Args:
            threshold: 掌握程度阈值，默认70%

        Returns:
            薄弱点列表
        """
        session = self.db.get_session()
        try:
            notes = (
                session.query(Note)
                .filter(Note.mastery_level < threshold)
                .order_by(Note.mastery_level)
                .all()
            )

            weak_points = []
            for note in notes:
                weak_points.append({
                    "note_id": note.id,
                    "title": note.title,
                    "algorithm_type": note.algorithm_type,
                    "mastery_level": note.mastery_level,
                    "review_count": note.review_count,
                    "last_reviewed": note.last_reviewed.isoformat() if note.last_reviewed else None,
                    "suggestion": self._generate_weak_point_suggestion(note)
                })

            return weak_points
        finally:
            session.close()

    def _generate_weak_point_suggestion(self, note: Note) -> str:
        """生成薄弱点学习建议

        根据笔记情况生成个性化的学习建议。

        Args:
            note: 笔记对象

        Returns:
            学习建议文本
        """
        suggestions = []

        if note.review_count == 0:
            suggestions.append("建议先完成首次复习")
        elif note.mastery_level < 30:
            suggestions.append("需要加强基础知识理解")
        elif note.mastery_level < 50:
            suggestions.append("建议多做相关练习题")
        else:
            suggestions.append("继续坚持复习巩固")

        if note.last_reviewed is None:
            suggestions.append("该知识点尚未复习，请尽快开始")
        elif (datetime.now() - note.last_reviewed).days > 7:
            suggestions.append("遗忘风险较高，请增加复习频率")

        return "；".join(suggestions)

    def start_review(self, note_id: int) -> Optional[Dict[str, Any]]:
        """开始复习

        为指定笔记创建或更新复习记录。

        Args:
            note_id: 笔记ID

        Returns:
            复习记录信息
        """
        session = self.db.get_session()
        try:
            note = session.query(Note).filter(Note.id == note_id).first()
            if not note:
                return None

            now = datetime.now()
            record = ReviewRecord(
                note_id=note_id,
                review_date=now,
                status="in_progress"
            )
            session.add(record)
            session.commit()
            session.refresh(record)

            return {
                "record_id": record.id,
                "note_id": note_id,
                "title": note.title,
                "content": note.content,
                "review_date": record.review_date.isoformat(),
                "status": record.status
            }
        finally:
            session.close()

    def complete_review(
        self,
        note_id: int,
        score: int,
        is_correct: bool,
        difficulty: str = "中等"
    ) -> Optional[Dict[str, Any]]:
        """完成复习

        完成复习后更新笔记状态、掌握程度和下次复习时间。

        Args:
            note_id: 笔记ID
            score: 复习得分（0-100）
            is_correct: 答题是否正确
            difficulty: 题目难度

        Returns:
            更新后的笔记信息
        """
        session = self.db.get_session()
        try:
            note = session.query(Note).filter(Note.id == note_id).first()
            if not note:
                return None

            pending_records = (
                session.query(ReviewRecord)
                .filter(
                    ReviewRecord.note_id == note_id,
                    ReviewRecord.status.in_(["pending", "in_progress"])
                )
                .all()
            )
            for record in pending_records:
                record.status = "completed"
                record.score = score

            new_mastery = self.forgotten_curve.update_mastery_level(
                note.mastery_level, is_correct, difficulty
            )

            note.mastery_level = new_mastery
            note.review_count += 1
            note.last_reviewed = datetime.now()

            next_review = self.forgotten_curve.calculate_next_review(
                new_mastery, note.review_count, datetime.now()
            )
            note.next_review_date = next_review.date()

            session.commit()
            session.refresh(note)

            return {
                "note_id": note.id,
                "title": note.title,
                "mastery_level": note.mastery_level,
                "review_count": note.review_count,
                "last_reviewed": note.last_reviewed.isoformat(),
                "next_review_date": note.next_review_date.isoformat(),
                "mastery_change": new_mastery - note.mastery_level + (new_mastery - note.mastery_level)
            }
        finally:
            session.close()

    def skip_review(self, note_id: int, reason: str = "") -> bool:
        """跳过复习

        将复习记录标记为跳过，并计算下次复习时间。

        Args:
            note_id: 笔记ID
            reason: 跳过原因

        Returns:
            是否成功
        """
        session = self.db.get_session()
        try:
            note = session.query(Note).filter(Note.id == note_id).first()
            if not note:
                return False

            pending_records = (
                session.query(ReviewRecord)
                .filter(
                    ReviewRecord.note_id == note_id,
                    ReviewRecord.status == "pending"
                )
                .all()
            )
            for record in pending_records:
                record.status = "skipped"

            short_interval = self.forgotten_curve.intervals[0]
            next_review = datetime.now() + timedelta(days=short_interval)
            note.next_review_date = next_review.date()

            session.commit()
            return True
        finally:
            session.close()

    def get_review_statistics(self, target_date: date = None) -> Dict[str, Any]:
        """获取复习统计

        获取指定日期的复习统计数据。

        Args:
            target_date: 目标日期，默认为今天

        Returns:
            统计信息字典
        """
        if target_date is None:
            target_date = date.today()

        session = self.db.get_session()
        try:
            total_notes = session.query(Note).count()

            overdue_notes = (
                session.query(Note)
                .filter(Note.next_review_date < target_date)
                .count()
            )

            due_today_notes = (
                session.query(Note)
                .filter(Note.next_review_date == target_date)
                .count()
            )

            weak_count = (
                session.query(Note)
                .filter(Note.mastery_level < 70)
                .count()
            )

            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())

            completed_today = (
                session.query(ReviewRecord)
                .filter(
                    ReviewRecord.review_date >= start_of_day,
                    ReviewRecord.review_date <= end_of_day,
                    ReviewRecord.status == "completed"
                )
                .count()
            )

            return {
                "date": target_date.isoformat(),
                "total_notes": total_notes,
                "overdue_count": overdue_notes,
                "due_today_count": due_today_notes,
                "completed_today": completed_today,
                "weak_points_count": weak_count
            }
        finally:
            session.close()

    def generate_review_plan_for_note(self, note_id: int) -> Optional[List[Dict[str, Any]]]:
        """为笔记生成复习计划

        根据笔记创建时间和遗忘曲线算法，生成未来复习时间表。

        Args:
            note_id: 笔记ID

        Returns:
            复习计划列表
        """
        session = self.db.get_session()
        try:
            note = session.query(Note).filter(Note.id == note_id).first()
            if not note:
                return None

            schedule = self.forgotten_curve.get_review_schedule(
                note_id, note.created_at
            )

            first_review_date = datetime.now()
            note.next_review_date = first_review_date.date()

            session.commit()

            return [
                {
                    "note_id": item["note_id"],
                    "review_date": item["review_date"].isoformat(),
                    "interval_days": item["interval"],
                    "is_key_review": item["is_key_review"]
                }
                for item in schedule
            ]
        finally:
            session.close()
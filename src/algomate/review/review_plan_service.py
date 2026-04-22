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

    def is_new_user(self) -> Dict[str, Any]:
        """检测是否为新手用户

        判断用户是否还没有添加任何笔记或尚未开始复习，
        以便提供新手引导。

        Returns:
            包含新手状态和推荐行动的字典
        """
        session = self.db.get_session()
        try:
            total_notes = session.query(Note).count()
            total_reviews = session.query(ReviewRecord).count()

            is_new = total_notes == 0
            has_started = total_reviews > 0

            if is_new:
                return {
                    "is_new_user": True,
                    "total_notes": 0,
                    "learning_days": 0,
                    "current_step": "add_first_note",
                    "message": "欢迎开始算法学习之旅！",
                    "next_action": {
                        "text": "添加第一个笔记",
                        "description": "点击上方「笔记」按钮，添加您要学习的算法笔记",
                        "action": "navigate_to_notes",
                        "icon": "📝"
                    },
                    "suggestions": [
                        {
                            "title": "从基础开始",
                            "content": "建议从排序算法、二分查找等基础内容开始学习"
                        },
                        {
                            "title": "循序渐进",
                            "content": "先理解原理，再做练习，最后复习巩固"
                        },
                        {
                            "title": "记录重点",
                            "content": "每学完一个知识点，记下核心思路和易错点"
                        }
                    ]
                }
            elif total_notes > 0 and not has_started:
                return {
                    "is_new_user": True,
                    "total_notes": total_notes,
                    "learning_days": 0,
                    "current_step": "start_first_review",
                    "message": "您已添加 {0} 个笔记，开始复习吧！".format(total_notes),
                    "next_action": {
                        "text": "开始首次复习",
                        "description": "您的学习之旅即将开始，点击开始复习来激活遗忘曲线",
                        "action": "start_review",
                        "icon": "🚀"
                    },
                    "suggestions": [
                        {
                            "title": "首次复习很重要",
                            "content": "根据艾宾浩斯遗忘曲线，首次复习应在学习后1天进行"
                        },
                        {
                            "title": "保持连续性",
                            "content": "每天坚持复习，学习效果会更好"
                        }
                    ]
                }
            else:
                return {
                    "is_new_user": False,
                    "total_notes": total_notes,
                    "learning_days": self._calculate_learning_days(),
                    "current_step": None,
                    "message": None,
                    "next_action": None,
                    "suggestions": []
                }
        finally:
            session.close()

    def _calculate_learning_days(self) -> int:
        """计算学习天数

        Returns:
            从第一条复习记录到现在的天数
        """
        session = self.db.get_session()
        try:
            first_review = (
                session.query(ReviewRecord)
                .order_by(ReviewRecord.review_date)
                .first()
            )
            if not first_review:
                return 0
            delta = datetime.now() - first_review.review_date
            return max(1, delta.days)
        finally:
            session.close()
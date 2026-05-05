"""
修炼计划服务模块

提供今日修炼计划相关的业务逻辑：
- 获取今日应修炼的卡牌列表
- 生成和管理修炼记录
- 更新修炼状态和领悟程度
- 获取薄弱点提醒
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy import func
from ..data.database import Database
from ..data.repositories.review_repo import ReviewRecordRepository
from algomate.models import ReviewRecord
from algomate.models.cards import Card
from ..core.memory.forgotten_curve import ForgottenCurveEngine


class ReviewPlanService:
    """修炼计划服务

    负责管理今日修炼计划的业务逻辑，包括：
    - 获取今日应修炼的卡牌
    - 创建修炼记录
    - 完成修炼后更新领悟程度
    - 识别薄弱点

    Attributes:
        db: 数据库实例
        review_repo: 修炼记录仓库
        forgotten_curve: 遗忘曲线算法
    """

    def __init__(self, db: Database = None):
        """初始化修炼计划服务

        Args:
            db: 数据库实例，默认使用单例
        """
        self.db = db or Database.get_instance()
        self.review_repo = ReviewRecordRepository(self.db)
        self.forgotten_curve = ForgottenCurveEngine()

    def get_today_review_plan(self, target_date: date = None) -> List[Dict[str, Any]]:
        """获取今日修炼计划

        获取指定日期应修炼的卡牌列表，包含卡牌信息和修炼状态。

        Args:
            target_date: 目标日期，默认为今天

        Returns:
            修炼计划列表，每项包含卡牌信息和修炼状态
        """
        if target_date is None:
            target_date = date.today()

        session = self.db.get_session()
        try:
            cards = (
                session.query(Card)
                .filter(Card.next_review_date <= target_date, Card.is_sealed == False)
                .order_by(Card.next_review_date)
                .all()
            )

            review_plan = []
            for card in cards:
                pending_records = (
                    session.query(ReviewRecord)
                    .filter(
                        ReviewRecord.card_id == card.id,
                        ReviewRecord.status == "pending"
                    )
                    .order_by(ReviewRecord.review_date)
                    .all()
                )

                review_plan.append({
                    "card_id": card.id,
                    "name": card.name,
                    "domain": card.domain,
                    "summary": card.summary or "",
                    "algorithm_type": card.algorithm_type,
                    "durability": card.durability,
                    "review_level": card.review_level,
                    "review_count": card.review_count,
                    "last_reviewed": card.last_reviewed.isoformat() if card.last_reviewed else None,
                    "next_review_date": card.next_review_date.isoformat() if card.next_review_date else None,
                    "pending_records": [
                        {"id": r.id, "review_date": r.review_date.isoformat(), "status": r.status}
                        for r in pending_records
                    ],
                    "is_overdue": card.next_review_date < target_date if card.next_review_date else False
                })

            return review_plan
        finally:
            session.close()

    def get_weak_points(self, threshold: int = 70) -> List[Dict[str, Any]]:
        """获取薄弱点提醒

        获取耐久度低于阈值的卡牌，作为薄弱点提醒。

        Args:
            threshold: 耐久度阈值，默认70

        Returns:
            薄弱点列表
        """
        session = self.db.get_session()
        try:
            cards = (
                session.query(Card)
                .filter(Card.durability < threshold, Card.is_sealed == False)
                .order_by(Card.durability)
                .all()
            )

            weak_points = []
            for card in cards:
                weak_points.append({
                    "card_id": card.id,
                    "name": card.name,
                    "algorithm_type": card.algorithm_type,
                    "durability": card.durability,
                    "review_count": card.review_count,
                    "last_reviewed": card.last_reviewed.isoformat() if card.last_reviewed else None,
                    "suggestion": self._generate_weak_point_suggestion(card)
                })

            return weak_points
        finally:
            session.close()

    def _generate_weak_point_suggestion(self, card: Card) -> str:
        """生成薄弱点修习建议

        根据卡牌情况生成个性化的修习建议。

        Args:
            card: 卡牌对象

        Returns:
            修习建议文本
        """
        suggestions = []

        if card.review_count == 0:
            suggestions.append("建议先完成首次修炼")
        elif card.durability < 30:
            suggestions.append("需要加强基础知识理解")
        elif card.durability < 50:
            suggestions.append("建议多做相关试炼题")
        else:
            suggestions.append("继续坚持修炼巩固")

        if card.last_reviewed is None:
            suggestions.append("该秘术尚未修炼，请尽快开始")
        elif (datetime.now() - card.last_reviewed).days > 7:
            suggestions.append("遗忘风险较高，请增加修炼频率")

        return "；".join(suggestions)

    def start_review(self, card_id: int) -> Optional[Dict[str, Any]]:
        """开始修炼

        为指定卡牌创建或更新修炼记录。

        Args:
            card_id: 卡牌ID

        Returns:
            修炼记录信息
        """
        session = self.db.get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                return None

            now = datetime.now()
            record = ReviewRecord(
                card_id=card_id,
                review_date=now,
                status="in_progress"
            )
            session.add(record)
            session.commit()
            session.refresh(record)

            return {
                "record_id": record.id,
                "card_id": card_id,
                "name": card.name,
                "knowledge_content": card.knowledge_content,
                "review_date": record.review_date.isoformat(),
                "status": record.status
            }
        finally:
            session.close()

    def complete_review(
        self,
        card_id: int,
        action: str = "success"
    ) -> Optional[Dict[str, Any]]:
        """完成修炼

        完成修炼后更新卡牌状态和下次修炼时间。

        Args:
            card_id: 卡牌ID
            action: 修炼动作（success/fail）

        Returns:
            更新后的卡牌信息
        """
        from ..core.memory.forgotten_curve import ReviewAction

        session = self.db.get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                return None

            pending_records = (
                session.query(ReviewRecord)
                .filter(
                    ReviewRecord.card_id == card_id,
                    ReviewRecord.status.in_(["pending", "in_progress"])
                )
                .all()
            )
            for record in pending_records:
                record.status = "completed"

            review_action = ReviewAction.SUCCESS if action == "success" else ReviewAction.FAIL
            new_level, next_review_date = self.forgotten_curve.complete_review_for_card(
                card, review_action
            )

            session.commit()
            session.refresh(card)

            return {
                "card_id": card.id,
                "name": card.name,
                "durability": card.durability,
                "review_level": card.review_level,
                "review_count": card.review_count,
                "last_reviewed": card.last_reviewed.isoformat() if card.last_reviewed else None,
                "next_review_date": card.next_review_date.isoformat() if card.next_review_date else None
            }
        finally:
            session.close()

    def skip_review(self, card_id: int, reason: str = "") -> bool:
        """跳过修炼

        将修炼记录标记为跳过，并计算下次修炼时间。

        Args:
            card_id: 卡牌ID
            reason: 跳过原因

        Returns:
            是否成功
        """
        session = self.db.get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                return False

            pending_records = (
                session.query(ReviewRecord)
                .filter(
                    ReviewRecord.card_id == card_id,
                    ReviewRecord.status == "pending"
                )
                .all()
            )
            for record in pending_records:
                record.status = "skipped"

            short_interval = self.forgotten_curve.intervals[0]
            next_review = datetime.now() + timedelta(days=short_interval)
            card.next_review_date = next_review

            session.commit()
            return True
        finally:
            session.close()

    def get_review_statistics(self, target_date: date = None) -> Dict[str, Any]:
        """获取修炼统计

        获取指定日期的修炼统计数据。

        Args:
            target_date: 目标日期，默认为今天

        Returns:
            统计信息字典
        """
        if target_date is None:
            target_date = date.today()

        session = self.db.get_session()
        try:
            total_cards = session.query(Card).filter(Card.is_sealed == False).count()

            overdue_cards = (
                session.query(Card)
                .filter(Card.next_review_date < target_date, Card.is_sealed == False)
                .count()
            )

            due_today_cards = (
                session.query(Card)
                .filter(Card.next_review_date == target_date, Card.is_sealed == False)
                .count()
            )

            weak_count = (
                session.query(Card)
                .filter(Card.durability < 70, Card.is_sealed == False)
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

            level_distribution_raw = (
                session.query(Card.review_level, func.count(Card.id))
                .filter(Card.is_sealed == False)
                .group_by(Card.review_level)
                .all()
            )
            review_level_distribution = {str(level): count for level, count in level_distribution_raw}

            seven_days_ago = datetime.combine(target_date - timedelta(days=7), datetime.min.time())
            end_of_target = datetime.combine(target_date, datetime.max.time())
            review_days_raw = (
                session.query(func.date(ReviewRecord.review_date))
                .filter(
                    ReviewRecord.review_date >= seven_days_ago,
                    ReviewRecord.review_date <= end_of_target,
                    ReviewRecord.status == "completed"
                )
                .distinct()
                .all()
            )
            weekly_review_days = len(review_days_raw)

            total_review_count = (
                session.query(ReviewRecord)
                .filter(ReviewRecord.status == "completed")
                .count()
            )

            return {
                "date": target_date.isoformat(),
                "total_cards": total_cards,
                "overdue_count": overdue_cards,
                "due_today_count": due_today_cards,
                "completed_today": completed_today,
                "weak_points_count": weak_count,
                "review_level_distribution": review_level_distribution,
                "weekly_review_days": weekly_review_days,
                "total_review_count": total_review_count,
            }
        finally:
            session.close()

    def generate_review_plan_for_card(self, card_id: int) -> Optional[List[Dict[str, Any]]]:
        """为卡牌生成修炼计划

        根据卡牌创建时间和遗忘曲线算法，生成未来修炼时间表。

        Args:
            card_id: 卡牌ID

        Returns:
            修炼计划列表
        """
        session = self.db.get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                return None

            schedule = []
            now = datetime.now()
            current_level = card.review_level

            for i, interval in enumerate(self.forgotten_curve.intervals):
                level = i + 1
                if level <= current_level:
                    continue
                review_date = now + timedelta(days=interval)
                schedule.append({
                    "card_id": card_id,
                    "review_date": review_date.isoformat(),
                    "interval_days": interval,
                    "review_level": level,
                    "is_key_review": level in [1, 3, 6]
                })

            first_review_date = now
            card.next_review_date = first_review_date

            session.commit()

            return schedule
        finally:
            session.close()

    def is_new_user(self) -> Dict[str, Any]:
        """检测是否为新手用户

        判断用户是否还没有获取任何卡牌或尚未开始修炼，
        以便提供新手引导。

        Returns:
            包含新手状态和推荐行动的字典
        """
        session = self.db.get_session()
        try:
            total_cards = session.query(Card).count()
            total_reviews = session.query(ReviewRecord).count()

            is_new = total_cards == 0
            has_started = total_reviews > 0

            if is_new:
                return {
                    "is_new_user": True,
                    "total_cards": 0,
                    "learning_days": 0,
                    "current_step": "get_first_card",
                    "message": "欢迎开始算法修习之旅！",
                    "next_action": {
                        "text": "获取第一张卡牌",
                        "description": "与NPC对话，获取您的第一张算法卡牌",
                        "action": "navigate_to_npc",
                        "icon": "🃏"
                    },
                    "suggestions": [
                        {
                            "title": "从基础开始",
                            "content": "建议从排序算法、二分查找等基础内容开始修习"
                        },
                        {
                            "title": "循序渐进",
                            "content": "先理解原理，再做试炼，最后修炼巩固"
                        },
                        {
                            "title": "记录重点",
                            "content": "每学完一个秘术，记下核心思路和易错点"
                        }
                    ]
                }
            elif total_cards > 0 and not has_started:
                return {
                    "is_new_user": True,
                    "total_cards": total_cards,
                    "learning_days": 0,
                    "current_step": "start_first_review",
                    "message": "您已拥有 {0} 张卡牌，开始修炼吧！".format(total_cards),
                    "next_action": {
                        "text": "开始首次修炼",
                    "description": "您的修习之旅即将开始，点击开始修炼来激活遗忘曲线",
                        "action": "start_review",
                        "icon": "🚀"
                    },
                    "suggestions": [
                        {
                            "title": "首次修炼很重要",
                            "content": "根据艾宾浩斯遗忘曲线，首次修炼应在修习后1天进行"
                        },
                        {
                            "title": "保持连续性",
                            "content": "每天坚持修炼，修习效果会更好"
                        }
                    ]
                }
            else:
                return {
                    "is_new_user": False,
                    "total_cards": total_cards,
                    "learning_days": self._calculate_learning_days(),
                    "current_step": None,
                    "message": None,
                    "next_action": None,
                    "suggestions": []
                }
        finally:
            session.close()

    def _calculate_learning_days(self) -> int:
        """计算修习天数

        Returns:
            从第一条修炼记录到现在的天数
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

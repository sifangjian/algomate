"""
修炼调度器模块

管理每日修炼任务生成和调度，包括：
- 生成每日修炼任务列表
- 获取未来修炼计划
- 执行每日修炼任务

修炼任务生成规则：
    1. 优先濒危卡牌（耐久度 < 30）
    2. 然后到期的遗忘曲线修炼卡牌
    3. 结合长期遗忘曲线和Boss挑战
    4. 根据游戏难度设置每日任务数量
"""

import asyncio
import logging

from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from apscheduler.schedulers.background import BackgroundScheduler

from algomate.data.database import Database
from algomate.models.cards import Card
from algomate.core.memory.forgotten_curve import ForgottenCurveEngine
from algomate.core.game.durability import DurabilityManager, DurabilityAction
from algomate.core.game.difficulty import DifficultyManager, DifficultyLevel
from algomate.config.settings import AppConfig

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """任务类型枚举"""
    CRITICAL_REVIEW = "critical_review"
    FORGETTING_CURVE_REVIEW = "forgetting_curve_review"
    BOSS_CHALLENGE = "boss_challenge"


@dataclass
class ReviewTask:
    """修炼任务数据结构"""
    task_id: str
    task_type: TaskType
    card_id: int
    card_name: str
    card_domain: str
    card_durability: int
    priority: str
    reason: str
    due_date: Optional[date] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "card_id": self.card_id,
            "card_name": self.card_name,
            "card_domain": self.card_domain,
            "card_durability": self.card_durability,
            "priority": self.priority,
            "reason": self.reason,
            "due_date": self.due_date.isoformat() if self.due_date else None
        }


class ReviewScheduler:
    """修炼调度器
    
    管理每日修炼任务的生成和调度。
    
    Attributes:
        db: 数据库实例
        forgotten_curve_engine: 遗忘曲线引擎
        durability_manager: 耐久度管理器
        difficulty_manager: 难度管理器
        config: 应用配置
    """
    
    def __init__(
        self,
        db: Optional[Database] = None,
        config: Optional[AppConfig] = None
    ):
        """初始化修炼调度器
        
        Args:
            db: 数据库实例，默认使用单例
            config: 应用配置，默认自动加载
        """
        self.db = db or Database.get_instance()
        self.config = config or AppConfig.load()
        self.forgotten_curve_engine = ForgottenCurveEngine()
        self.durability_manager = DurabilityManager()
        self.difficulty_manager = DifficultyManager()
        self._scheduler = None
        self._scheduler_hour = 9
        self._scheduler_minute = 0

    def start(self):
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            self._execute_scheduled_daily_review,
            trigger='cron',
            hour=self._scheduler_hour,
            minute=self._scheduler_minute
        )
        self._scheduler.start()
        logger.info("Review scheduler started (daily at %02d:%02d)", self._scheduler_hour, self._scheduler_minute)

    def stop(self):
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("Review scheduler stopped")

    def _execute_scheduled_daily_review(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.execute_daily_review())
                    count = future.result()
            else:
                count = loop.run_until_complete(self.execute_daily_review())
            logger.info("Scheduled daily review completed, processed %d cards", count)
        except Exception:
            logger.exception("Error executing scheduled daily review")
    
    def generate_daily_tasks(
        self,
        user_id: Optional[int] = None
    ) -> List[ReviewTask]:
        """生成每日修炼任务
        
        Args:
            user_id: 用户ID（可选，当前系统为单用户）
        
        Returns:
            修炼任务列表
        
        Example:
            >>> scheduler = ReviewScheduler()
            >>> tasks = scheduler.generate_daily_tasks()
            >>> print(len(tasks))
            5
            >>> print(tasks[0].task_type)
            "critical_review"
        """
        session = self.db.get_session()
        try:
            all_cards = session.query(Card).filter(Card.is_sealed == False).all()
            
            tasks = []
            task_counter = 1
            
            critical_cards = [
                card for card in all_cards
                if self.durability_manager.is_critical(card.durability)
            ]
            
            for card in critical_cards:
                tasks.append(ReviewTask(
                    task_id=f"review_{task_counter}",
                    task_type=TaskType.CRITICAL_REVIEW,
                    card_id=card.id,
                    card_name=card.name,
                    card_domain=card.domain,
                    card_durability=card.durability,
                    priority="critical",
                    reason="濒危卡牌",
                    due_date=date.today()
                ))
                task_counter += 1
            
            due_cards = self.forgotten_curve_engine.get_daily_review_tasks(all_cards)
            
            for card in due_cards:
                if card not in critical_cards:
                    review_status = self.forgotten_curve_engine.get_review_status(
                        card.created_at,
                        card.last_reviewed,
                        getattr(card, 'review_level', 0)
                    )
                    
                    tasks.append(ReviewTask(
                        task_id=f"review_{task_counter}",
                        task_type=TaskType.FORGETTING_CURVE_REVIEW,
                        card_id=card.id,
                        card_name=card.name,
                        card_domain=card.domain,
                        card_durability=card.durability,
                        priority="high" if review_status.is_due else "medium",
                        reason="遗忘曲线修炼",
                        due_date=review_status.next_review_date
                    ))
                    task_counter += 1
            
            daily_task_count = self.difficulty_manager.get_daily_task_count()
            
            if len(tasks) < daily_task_count:
                remaining_slots = daily_task_count - len(tasks)
                
                non_critical_cards = [
                    card for card in all_cards
                    if card not in critical_cards and card not in due_cards
                ]
                
                non_critical_cards.sort(key=lambda c: c.durability)
                
                for card in non_critical_cards[:remaining_slots]:
                    tasks.append(ReviewTask(
                        task_id=f"review_{task_counter}",
                        task_type=TaskType.BOSS_CHALLENGE,
                        card_id=card.id,
                        card_name=card.name,
                        card_domain=card.domain,
                        card_durability=card.durability,
                        priority="low",
                        reason="Boss挑战",
                        due_date=date.today()
                    ))
                    task_counter += 1
            
            tasks.sort(key=lambda t: (
                0 if t.priority == "critical" else (1 if t.priority == "high" else 2),
                t.card_durability
            ))
            
            return tasks[:daily_task_count]
        finally:
            session.close()
    
    def get_upcoming_reviews(
        self,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """获取未来N天需要修炼的卡牌
        
        Args:
            days: 查询的天数范围
        
        Returns:
            修炼计划列表
        
        Example:
            >>> scheduler = ReviewScheduler()
            >>> reviews = scheduler.get_upcoming_reviews(7)
            >>> print(len(reviews))
            10
        """
        session = self.db.get_session()
        try:
            end_date = datetime.now().date() + timedelta(days=days)
            
            all_cards = session.query(Card).filter(Card.is_sealed == False).all()
            
            upcoming_reviews = []
            
            for card in all_cards:
                review_status = self.forgotten_curve_engine.get_review_status(
                    card.created_at,
                    card.last_reviewed,
                    getattr(card, 'review_level', 0)
                )
                
                if review_status.next_review_date <= end_date:
                    upcoming_reviews.append({
                        "card_id": card.id,
                        "card_name": card.name,
                        "card_domain": card.domain,
                        "card_durability": card.durability,
                        "review_date": review_status.next_review_date.isoformat(),
                        "review_level": review_status.review_level,
                        "is_due": review_status.is_due
                    })
            
            upcoming_reviews.sort(key=lambda r: r["review_date"])
            
            return upcoming_reviews
        finally:
            session.close()
    
    async def execute_daily_review(self) -> int:
        """执行每日修炼任务（定时调用）
        
        Returns:
            执行的任务数量
        
        Example:
            >>> scheduler = ReviewScheduler()
            >>> count = await scheduler.execute_daily_review()
            >>> print(f"执行了 {count} 个修炼任务")
        """
        tasks = self.generate_daily_tasks()
        
        session = self.db.get_session()
        try:
            for task in tasks:
                card = session.query(Card).filter(Card.id == task.card_id).first()
                if card:
                    new_durability, is_critical, is_sealed = self.durability_manager.update_durability(
                        current_durability=card.durability,
                        action=DurabilityAction.DAILY_DECAY,
                        difficulty=self.difficulty_manager.current_difficulty.value
                    )
                    
                    card.durability = new_durability
                    card.is_sealed = is_sealed
                    card.last_reviewed = datetime.now()
            
            session.commit()
            
            return len(tasks)
        finally:
            session.close()
    
    def get_review_statistics(self) -> Dict[str, Any]:
        """获取修炼统计数据
        
        Returns:
            统计数据字典
        """
        session = self.db.get_session()
        try:
            all_cards = session.query(Card).all()
            
            total_cards = len(all_cards)
            sealed_cards = len([c for c in all_cards if c.is_sealed])
            critical_cards = len([
                c for c in all_cards
                if not c.is_sealed and self.durability_manager.is_critical(c.durability)
            ])
            
            due_cards = self.forgotten_curve_engine.get_daily_review_tasks([
                c for c in all_cards if not c.is_sealed
            ])
            
            return {
                "total_cards": total_cards,
                "sealed_cards": sealed_cards,
                "critical_cards": critical_cards,
                "due_cards": len(due_cards),
                "active_cards": total_cards - sealed_cards,
                "health_rate": (total_cards - sealed_cards - critical_cards) / total_cards if total_cards > 0 else 0
            }
        finally:
            session.close()
    
    def get_domain_review_stats(self) -> List[Dict[str, Any]]:
        """获取各领域的修炼统计
        
        Returns:
            各领域统计数据列表
        """
        session = self.db.get_session()
        try:
            all_cards = session.query(Card).filter(Card.is_sealed == False).all()
            
            domain_stats = {}
            
            for card in all_cards:
                if card.domain not in domain_stats:
                    domain_stats[card.domain] = {
                        "domain": card.domain,
                        "total_count": 0,
                        "critical_count": 0,
                        "due_count": 0,
                        "avg_durability": 0
                    }
                
                domain_stats[card.domain]["total_count"] += 1
                
                if self.durability_manager.is_critical(card.durability):
                    domain_stats[card.domain]["critical_count"] += 1
                
                review_status = self.forgotten_curve_engine.get_review_status(
                    card.created_at,
                    card.last_reviewed,
                    getattr(card, 'review_level', 0)
                )
                
                if review_status.is_due:
                    domain_stats[card.domain]["due_count"] += 1
            
            for domain, stats in domain_stats.items():
                domain_cards = [c for c in all_cards if c.domain == domain]
                if domain_cards:
                    stats["avg_durability"] = sum(c.durability for c in domain_cards) / len(domain_cards)
            
            return list(domain_stats.values())
        finally:
            session.close()

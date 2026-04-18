"""
复习调度器模块

提供定时复习提醒功能，包括：
- 定时任务的启动和停止
- 每日复习邮件的发送
- 复习计划的管理
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from ...data.models import Note
from ...data.database import Database
from ...data.repositories import NoteRepository, ReviewRecordRepository
from algomate.config.settings import AppConfig
from ..memory.forgotten_curve import ForgottenCurve
from .email_sender import EmailSender


class ReviewScheduler:
    """复习调度器

    管理定时复习任务，包括每日邮件提醒的调度和执行。

    使用 APScheduler 实现后台定时任务，支持：
    - 每日定时发送复习提醒邮件
    - 自动创建复习记录
    - 查询即将到来的复习计划

    Attributes:
        config: 应用配置
        db: 数据库实例
        note_repo: 笔记仓库
        review_repo: 复习记录仓库
        email_sender: 邮件发送器
        forgotten_curve: 遗忘曲线算法
        scheduler: APScheduler 实例
    """

    def __init__(self, config: AppConfig, db: Database):
        """初始化调度器

        Args:
            config: 应用配置
            db: 数据库实例
        """
        self.config = config
        self.db = db
        self.note_repo = NoteRepository(db)
        self.review_repo = ReviewRecordRepository(db)
        self.email_sender = EmailSender(config)
        self.forgotten_curve = ForgottenCurve()
        self.scheduler = BackgroundScheduler()

    def start(self):
        """启动调度器

        如果配置启用了复习提醒，则启动定时任务。
        """
        if self.config.REVIEW_ENABLED:
            hour, minute = map(int, self.config.REVIEW_TIME.split(":"))
            self.scheduler.add_job(
                self.send_daily_review_email,
                CronTrigger(hour=hour, minute=minute),
                id="daily_review_email",
                replace_existing=True,
            )
            self.scheduler.start()

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()

    def send_daily_review_email(self):
        """发送每日复习邮件

        获取今日待复习的笔记，生成邮件内容并发送。
        """
        today = datetime.now().date()
        notes_due = self.note_repo.get_notes_due_for_review(today)

        if not notes_due:
            return

        email_content = self._build_email_content(notes_due)
        self.email_sender.send(email_content)

        for note in notes_due:
            self._create_review_record(note, today)

    def _build_email_content(self, notes: List[Note]) -> Dict[str, str]:
        """构建邮件内容

        Args:
            notes: 待复习的笔记列表

        Returns:
            包含主题和正文的字典
        """
        subject = "📚 算法学习助手 - 今日复习提醒"

        overview = f"今日复习目标：{len(notes)}个知识点\n"
        overview += f"预计用时：{len(notes) * 8}分钟\n\n"

        details = ""
        for i, note in enumerate(notes, 1):
            details += f"{'━' * 40}\n"
            details += f"📖 知识点 {i}：{note.title}\n"
            details += f"{'━' * 40}\n"
            details += f"{note.content}\n\n"

        body = f"亲爱的学习者，您好！\n\n{overview}\n{details}"
        body += "\n坚持复习，打卡学习！"

        return {"subject": subject, "body": body}

    def _create_review_record(self, note: Note, review_date: datetime):
        """创建复习记录

        Args:
            note: 笔记对象
            review_date: 复习日期
        """
        self.review_repo.create(
            note_id=note.id,
            review_date=review_date,
            status="pending",
        )

    def get_upcoming_reviews(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取即将到来的复习计划

        Args:
            days: 查询的天数范围

        Returns:
            复习计划列表
        """
        end_date = datetime.now().date() + timedelta(days=days)
        notes = self.note_repo.get_notes_due_for_review(end_date)

        schedule = []
        for note in notes:
            schedule.append({
                "note": note,
                "review_date": note.next_review_date,
            })
        return schedule

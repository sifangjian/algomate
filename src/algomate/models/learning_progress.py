"""
修为模型

记录用户每日的修习统计数据
"""

from datetime import date as date_type
from sqlalchemy import Column, Integer, Date

from algomate.data.database import Base


class LearningProgress(Base):
    """修为模型

    记录用户每日的修习统计数据。

    Attributes:
        id: 记录唯一标识
        date: 日期（唯一）
        notes_count: 当日新增心得数
        review_count: 当日修炼试炼数
        correct_count: 当日正确应战数
        total_count: 当日总应战数
    """
    __tablename__ = "learning_progress"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    notes_count = Column(Integer, default=0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    correct_count = Column(Integer, default=0, nullable=False)
    total_count = Column(Integer, default=0, nullable=False)

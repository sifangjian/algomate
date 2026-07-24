from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint

from algomate.data.database import Base


class TopicPrerequisite(Base):
    """算法主题前置依赖关系（动态，用户创建卡牌时生成）"""
    __tablename__ = "topic_prerequisites"
    __table_args__ = (
        UniqueConstraint("topic", "prerequisite", name="uq_topic_prerequisite"),
        {'extend_existing': True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(100), nullable=False, index=True)
    prerequisite = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

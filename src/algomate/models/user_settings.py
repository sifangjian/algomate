"""
用户设置模型

存储用户配置（游戏难度、邮件设置、API Key等）
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from algomate.data.database import Base


class UserSetting(Base):
    """用户设置模型

    存储用户的个性化设置项，采用键值对形式存储。

    Attributes:
        id: 设置项唯一标识
        key: 设置项名称（唯一）
        value: 设置值
        updated_at: 更新时间
    """
    __tablename__ = "user_settings"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, default="", nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

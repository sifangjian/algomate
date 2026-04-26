"""
用户设置模型

存储用户配置（游戏难度、邮件设置、API Key等）
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

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


class UserSettingCreate(BaseModel):
    """创建用户设置的输入验证模型"""
    key: str = Field(..., min_length=1, max_length=100, description="配置项名称")
    value: str = Field(default="", description="配置值")
    
    class Config:
        from_attributes = True


class UserSettingUpdate(BaseModel):
    """更新用户设置的输入验证模型"""
    value: str = Field(..., description="配置值")
    
    class Config:
        from_attributes = True


class UserSettingResponse(BaseModel):
    """返回给前端的用户设置数据模型"""
    id: int
    key: str
    value: str
    updated_at: datetime
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/settings", tags=["用户设置"])


@router.get("/", response_model=list[UserSettingResponse])
async def get_all_settings():
    """获取所有用户设置"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        settings = session.query(UserSetting).all()
        return settings
    finally:
        session.close()


@router.get("/{key}", response_model=UserSettingResponse)
async def get_setting(key: str):
    """获取单个用户设置"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        setting = session.query(UserSetting).filter(UserSetting.key == key).first()
        if not setting:
            raise HTTPException(status_code=404, detail=f"设置项 '{key}' 不存在")
        return setting
    finally:
        session.close()


@router.post("/", response_model=UserSettingResponse, status_code=201)
async def create_setting(setting: UserSettingCreate):
    """创建用户设置"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        existing = session.query(UserSetting).filter(UserSetting.key == setting.key).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"设置项 '{setting.key}' 已存在")
        
        new_setting = UserSetting(
            key=setting.key,
            value=setting.value
        )
        session.add(new_setting)
        session.commit()
        session.refresh(new_setting)
        return new_setting
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"创建设置失败: {str(e)}")
    finally:
        session.close()


@router.put("/{key}", response_model=UserSettingResponse)
async def update_setting(key: str, setting: UserSettingUpdate):
    """更新用户设置"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        existing = session.query(UserSetting).filter(UserSetting.key == key).first()
        if not existing:
            raise HTTPException(status_code=404, detail=f"设置项 '{key}' 不存在")
        
        existing.value = setting.value
        existing.updated_at = datetime.now()
        session.commit()
        session.refresh(existing)
        return existing
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新设置失败: {str(e)}")
    finally:
        session.close()


@router.delete("/{key}", status_code=204)
async def delete_setting(key: str):
    """删除用户设置"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        setting = session.query(UserSetting).filter(UserSetting.key == key).first()
        if not setting:
            raise HTTPException(status_code=404, detail=f"设置项 '{key}' 不存在")
        
        session.delete(setting)
        session.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除设置失败: {str(e)}")
    finally:
        session.close()


@router.post("/batch", status_code=201)
async def batch_update_settings(settings: dict[str, str]):
    """批量更新用户设置"""
    from algomate.data.database import Database
    
    db = Database.get_instance()
    session = db.get_session()
    try:
        for key, value in settings.items():
            existing = session.query(UserSetting).filter(UserSetting.key == key).first()
            if existing:
                existing.value = value
                existing.updated_at = datetime.now()
            else:
                new_setting = UserSetting(key=key, value=value)
                session.add(new_setting)
        
        session.commit()
        return {"message": "批量更新成功", "count": len(settings)}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"批量更新失败: {str(e)}")
    finally:
        session.close()

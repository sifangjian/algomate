from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from algomate.data.database import Database
from algomate.data.repositories.settings_repo import SettingsRepository

router = APIRouter(prefix="/settings", tags=["用户设置"])


class UpdateSettingsRequest(BaseModel):
    onboarding_completed: Optional[bool] = Field(None, description="引导是否已完成")
    api_key: Optional[str] = Field(None, description="智谱 API Key")
    api_key_configured: Optional[bool] = Field(None, description="API Key 是否已配置")
    theme: Optional[str] = Field(None, description="主题（light/dark）")
    language: Optional[str] = Field(None, description="语言")


def _success_response(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


@router.get("")
async def get_settings():
    db = Database.get_instance()
    session = db.get_session()
    try:
        repo = SettingsRepository(session)
        settings = repo.get_settings()
        return _success_response(data=settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设置失败: {str(e)}")
    finally:
        session.close()


@router.put("")
async def update_settings(request: UpdateSettingsRequest):
    db = Database.get_instance()
    session = db.get_session()
    try:
        repo = SettingsRepository(session)
        update_data = request.model_dump(exclude_unset=True)

        if "api_key" in update_data:
            api_key = update_data.pop("api_key")
            if api_key:
                update_data["api_key_configured"] = True
            else:
                update_data["api_key_configured"] = False

        if not update_data:
            return _success_response(data={"updated": True})

        try:
            result = repo.update_settings(update_data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"code": 40001, "message": str(e)})

        return _success_response(data=result)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新设置失败: {str(e)}")
    finally:
        session.close()

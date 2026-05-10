from typing import Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from algomate.data.database import Database
from algomate.data.repositories.settings_repo import SettingsRepository

router = APIRouter(prefix="/settings", tags=["用户设置"])
logger = logging.getLogger(__name__)


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
        logger.error("get_settings failed: %s", e, exc_info=True)
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
        logger.error("update_settings failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新设置失败: {str(e)}")
    finally:
        session.close()


@router.post("/legacy")
async def save_settings_legacy(settings: dict):
    from algomate.config.settings import AppConfig
    config = AppConfig.load()
    if "api_key" in settings:
        config.LLM_API_KEY = settings["api_key"]
    if "email_host" in settings:
        config.SMTP_HOST = settings["email_host"]
    if "email_port" in settings:
        config.SMTP_PORT = settings["email_port"]
    if "email_username" in settings:
        config.SMTP_USER = settings["email_username"]
    if "email_password" in settings and settings["email_password"]:
        config.SMTP_PASSWORD = settings["email_password"]
    if "review_time" in settings:
        config.REVIEW_TIME = settings["review_time"]
    if "forgetting_curve_param" in settings:
        param = settings["forgetting_curve_param"]
        config.REVIEW_INTERVALS = [1, 3, 7, 14, 30, param]
    config.save()
    return {"message": "设置保存成功"}


@router.post("/test-api")
async def test_api_key(apiKey: dict):
    api_key = apiKey.get("apiKey", "")
    if not api_key:
        return {"success": False, "message": "API密钥不能为空"}

    try:
        import os
        os.environ["OPENAI_API_KEY"] = api_key
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-3.5-turbo", max_tokens=10)
        response = llm.invoke("Hello")
        return {"success": True, "message": "API密钥有效"}
    except Exception as e:
        logger.warning("test_api_key failed: %s", e)
        return {"success": False, "message": f"API密钥无效: {str(e)}"}


@router.post("/test-email")
async def test_email_config(emailConfig: dict):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    host = emailConfig.get("host")
    port = emailConfig.get("port", 587)
    username = emailConfig.get("username")
    password = emailConfig.get("password")
    to_email = emailConfig.get("to_email")

    if not all([host, port, username, password, to_email]):
        return {"success": False, "message": "邮件配置不完整"}

    try:
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_email
        msg['Subject'] = "Algomate 邮件测试"
        msg.attach(MIMEText("这是一封来自Algomate的测试邮件", 'plain'))

        server = smtplib.SMTP(host, int(port))
        server.starttls()
        server.login(username, password)
        server.sendmail(username, [to_email], msg.as_string())
        server.quit()
        return {"success": True, "message": "邮件发送成功"}
    except Exception as e:
        logger.error("test_email failed: %s", e, exc_info=True)
        return {"success": False, "message": f"邮件发送失败: {str(e)}"}

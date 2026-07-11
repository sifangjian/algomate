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
    model: Optional[str] = Field(None, description="模型名称")
    api_base_url: Optional[str] = Field(None, description="API 基础 URL")
    theme: Optional[str] = Field(None, description="主题（light/dark）")
    language: Optional[str] = Field(None, description="语言")
    api_config_enabled: Optional[bool] = Field(None, description="是否启用自定义API配置")


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

        # 处理API key状态标记，但不从update_data中移除api_key
        if "api_key" in update_data:
            api_key = update_data["api_key"]
            if api_key:
                update_data["api_key_configured"] = True
            else:
                update_data["api_key_configured"] = False

        if not update_data:
            return _success_response(data={"updated": True})

        try:
            result = repo.update_settings(update_data)

            # 处理API配置启用/禁用
            if "api_config_enabled" in update_data:
                from algomate.config.settings import AppConfig
                import logging
                logger = logging.getLogger(__name__)

                config = AppConfig.get()

                if request.api_config_enabled and request.model and request.api_key:
                    # 启用自定义API配置
                    old_model = config.LLM_MODEL
                    old_base_url = config.LLM_BASE_URL

                    config.LLM_MODEL = request.model
                    config.LLM_BASE_URL = request.api_base_url or "https://open.bigmodel.cn/api/paas/v4"
                    config.LLM_API_KEY = request.api_key
                    config.save()

                    # 重新加载配置，确保立即生效
                    AppConfig.reload()

                    logger.info(f"🔄 自定义API配置已启用并重新加载 | 模型: {old_model} → {request.model} | Base URL: {old_base_url} → {config.LLM_BASE_URL}")

                elif not request.api_config_enabled:
                    # 禁用自定义API配置，恢复默认配置
                    old_model = config.LLM_MODEL
                    old_base_url = config.LLM_BASE_URL
                    old_api_key = config.LLM_API_KEY

                    # 恢复默认配置，但不清空API key（保留在数据库中供下次启用使用）
                    config.LLM_MODEL = "glm-4.7-flash"
                    config.LLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
                    config.LLM_API_KEY = ""  # 清空配置文件中的API key，让其从环境变量加载
                    config.save()

                    # 重新加载配置，确保立即生效
                    AppConfig.reload()

                    logger.info(f"🔄 已切换为默认配置 | 模型: {old_model} → glm-4.7-flash | Base URL: {old_base_url} → https://open.bigmodel.cn/api/paas/v4")

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
async def test_api_key(test_data: dict):
    """测试API连接"""
    import httpx

    api_key = test_data.get("apiKey", "")
    model = test_data.get("model", "glm-4.7-flash")
    api_base_url = test_data.get("apiBaseUrl", "https://open.bigmodel.cn/api/paas/v4")

    if not api_key:
        return {"success": False, "message": "API密钥不能为空"}

    try:
        logger.info(f"🧪 测试API连接 | 模型: {model} | Base URL: {api_base_url}")

        # 使用简单的HTTP请求测试API key，而不是调用完整的LLM
        # 这样可以更快响应，避免长时间等待
        test_url = f"{api_base_url.rstrip('/')}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 发送一个最简单的请求测试认证
        test_payload = {
            "model": model,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(test_url, json=test_payload, headers=headers)

            if response.status_code == 200:
                logger.info(f"✅ API连接测试成功 | 模型: {model}")
                return {"success": True, "message": "API密钥有效"}
            elif response.status_code == 401:
                error_msg = "API密钥无效或已过期"
                logger.error(f"❌ API连接测试失败 | 模型: {model} | 错误: {error_msg}")
                return {"success": False, "message": error_msg}
            else:
                error_detail = response.json().get("error", {}).get("message", "未知错误")
                logger.error(f"❌ API连接测试失败 | 模型: {model} | 状态码: {response.status_code} | 错误: {error_detail}")
                return {"success": False, "message": f"API请求失败: {error_detail}"}

    except httpx.TimeoutException:
        logger.error(f"❌ API连接测试超时 | 模型: {model}")
        return {"success": False, "message": "连接超时，请检查API地址或网络"}
    except Exception as e:
        logger.error(f"❌ API连接测试失败 | 模型: {model} | 错误: {str(e)}")
        return {"success": False, "message": f"测试失败: {str(e)}"}


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

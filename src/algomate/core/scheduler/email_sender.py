"""
邮件提醒系统模块

发送每日复习提醒邮件，包括：
- 发送复习提醒邮件
- 测试邮件配置
- 定时任务：每日发送提醒

邮件内容模板：
    主题: 【算法大陆】冒险者，今日的修炼任务已准备就绪！
    正文:
        尊敬的大陆冒险者，
        
        根据您的修炼进度，以下是今日的复习任务：
        
        📋 今日任务（3项）
        1. 【濒危卡牌】二分查找（耐久度: 28）
           → 建议立即复习，避免卡牌消散
        2. 【遗忘复习】滑动窗口（到期: 今天）
           → 您的记忆正在淡去，快来复习吧！
        3. 【Boss挑战】迷雾史莱姆王
           → 使用「滑动窗口」卡牌应战
        
        点击此处进入冒险: http://localhost:3000
        
        祝您修行顺利！
        —— 算法大陆 AI导师
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from algomate.config.settings import AppConfig
from algomate.core.scheduler.review_scheduler import ReviewScheduler, ReviewTask, TaskType


class EmailSender:
    """邮件提醒系统
    
    负责发送每日复习提醒邮件。
    
    Attributes:
        config: 应用配置
        review_scheduler: 复习调度器
    """
    
    def __init__(
        self,
        config: Optional[AppConfig] = None,
        review_scheduler: Optional[ReviewScheduler] = None
    ):
        """初始化邮件提醒系统
        
        Args:
            config: 应用配置，默认自动加载
            review_scheduler: 复习调度器，默认自动创建
        """
        self.config = config or AppConfig.load()
        self.review_scheduler = review_scheduler or ReviewScheduler()
    
    def send_review_reminder(
        self,
        recipients: List[str],
        tasks: Optional[List[ReviewTask]] = None
    ) -> bool:
        """发送复习提醒邮件
        
        Args:
            recipients: 收件人邮箱列表
            tasks: 复习任务列表，默认自动生成
        
        Returns:
            是否发送成功
        
        Raises:
            ValueError: 当邮件配置不完整时
        
        Example:
            >>> sender = EmailSender()
            >>> success = sender.send_review_reminder(["user@example.com"])
            >>> print("发送成功" if success else "发送失败")
        """
        if not self._validate_email_config():
            raise ValueError("邮件配置不完整，请检查SMTP设置")
        
        if tasks is None:
            tasks = self.review_scheduler.generate_daily_tasks()
        
        if not tasks:
            return False
        
        email_content = self._build_email_content(tasks)
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = email_content["subject"]
            message["From"] = self.config.EMAIL_FROM or self.config.SMTP_USER
            message["To"] = ", ".join(recipients)
            
            text_part = MIMEText(email_content["body"], "plain", "utf-8")
            message.attach(text_part)
            
            html_body = self._convert_to_html(email_content["body"])
            html_part = MIMEText(html_body, "html", "utf-8")
            message.attach(html_part)
            
            with smtplib.SMTP_SSL(self.config.SMTP_HOST, self.config.SMTP_PORT) as server:
                server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
                server.send_message(message)
            
            return True
        except Exception as e:
            print(f"发送邮件失败: {str(e)}")
            return False
    
    def test_email_config(self) -> Dict[str, Any]:
        """测试邮件配置是否正确
        
        Returns:
            测试结果字典
        
        Example:
            >>> sender = EmailSender()
            >>> result = sender.test_email_config()
            >>> print(result["success"])
            True
        """
        result = {
            "success": False,
            "message": "",
            "details": {}
        }
        
        if not self._validate_email_config():
            result["message"] = "邮件配置不完整"
            result["details"] = {
                "smtp_host": self.config.SMTP_HOST or "未配置",
                "smtp_port": self.config.SMTP_PORT or "未配置",
                "smtp_user": self.config.SMTP_USER or "未配置",
                "smtp_password": "***" if self.config.SMTP_PASSWORD else "未配置",
                "email_from": self.config.EMAIL_FROM or "未配置"
            }
            return result
        
        try:
            with smtplib.SMTP_SSL(self.config.SMTP_HOST, self.config.SMTP_PORT) as server:
                server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
            
            result["success"] = True
            result["message"] = "邮件配置正确，连接测试成功"
            result["details"] = {
                "smtp_host": self.config.SMTP_HOST,
                "smtp_port": self.config.SMTP_PORT,
                "smtp_user": self.config.SMTP_USER,
                "connection": "SSL连接成功"
            }
        except smtplib.SMTPAuthenticationError:
            result["message"] = "SMTP认证失败，请检查用户名和密码"
        except smtplib.SMTPConnectError:
            result["message"] = "无法连接到SMTP服务器，请检查主机和端口"
        except Exception as e:
            result["message"] = f"测试失败: {str(e)}"
        
        return result
    
    async def scheduled_daily_reminder(self) -> int:
        """定时任务：每日发送提醒
        
        Returns:
            发送的邮件数量
        
        Example:
            >>> sender = EmailSender()
            >>> count = await sender.scheduled_daily_reminder()
            >>> print(f"发送了 {count} 封邮件")
        """
        tasks = self.review_scheduler.generate_daily_tasks()
        
        if not tasks:
            return 0
        
        recipients = self._get_recipients()
        
        if not recipients:
            return 0
        
        success = self.send_review_reminder(recipients, tasks)
        
        return 1 if success else 0
    
    def preview_email_content(self) -> Dict[str, str]:
        """预览今日提醒邮件内容
        
        Returns:
            包含主题和正文的字典
        
        Example:
            >>> sender = EmailSender()
            >>> content = sender.preview_email_content()
            >>> print(content["subject"])
        """
        tasks = self.review_scheduler.generate_daily_tasks()
        return self._build_email_content(tasks)
    
    def _build_email_content(self, tasks: List[ReviewTask]) -> Dict[str, str]:
        """构建邮件内容
        
        Args:
            tasks: 复习任务列表
        
        Returns:
            包含主题和正文的字典
        """
        subject = "【算法大陆】冒险者，今日的修炼任务已准备就绪！"
        
        critical_tasks = [t for t in tasks if t.task_type == TaskType.CRITICAL_REVIEW]
        review_tasks = [t for t in tasks if t.task_type == TaskType.FORGETTING_CURVE_REVIEW]
        boss_tasks = [t for t in tasks if t.task_type == TaskType.BOSS_CHALLENGE]
        
        body = f"""尊敬的大陆冒险者，

根据您的修炼进度，以下是今日的复习任务：

📋 今日任务（{len(tasks)}项）
"""
        
        task_num = 1
        
        for task in critical_tasks:
            body += f"""
{task_num}. 【濒危卡牌】{task.card_name}（耐久度: {task.card_durability}）
   → 建议立即复习，避免卡牌消散
"""
            task_num += 1
        
        for task in review_tasks:
            due_text = "今天" if task.due_date == datetime.now().date() else task.due_date.strftime("%m月%d日")
            body += f"""
{task_num}. 【遗忘复习】{task.card_name}（到期: {due_text}）
   → 您的记忆正在淡去，快来复习吧！
"""
            task_num += 1
        
        for task in boss_tasks:
            body += f"""
{task_num}. 【Boss挑战】{task.card_domain}守护者
   → 使用「{task.card_name}」卡牌应战
"""
            task_num += 1
        
        body += f"""
点击此处进入冒险: {self.config.APP_URL or 'http://localhost:3000'}

祝您修行顺利！
—— 算法大陆 AI导师
"""
        
        return {
            "subject": subject,
            "body": body
        }
    
    def _convert_to_html(self, text: str) -> str:
        """将纯文本转换为HTML
        
        Args:
            text: 纯文本内容
        
        Returns:
            HTML格式的内容
        """
        html = text
        html = html.replace("\n\n", "</p><p>")
        html = f"<p>{html}</p>"
        html = re.sub(r"```([\s\S]*?)```", r"<pre><code>\1</code></pre>", html)
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
        html = re.sub(r"━+", "<hr>", html)
        
        html = html.replace("📋", "<span style='font-size: 1.2em;'>📋</span>")
        html = html.replace("【", "<strong>【")
        html = html.replace("】", "】</strong>")
        html = html.replace("→", "<span style='color: #666;'>→</span>")
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        p {{
            margin: 10px 0;
        }}
        strong {{
            color: #2c5282;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        code {{
            background-color: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }}
        hr {{
            border: none;
            border-top: 1px solid #e0e0e0;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    {html}
</body>
</html>
"""
    
    def _validate_email_config(self) -> bool:
        """验证邮件配置是否完整
        
        Returns:
            配置是否完整
        """
        return all([
            self.config.SMTP_HOST,
            self.config.SMTP_PORT,
            self.config.SMTP_USER,
            self.config.SMTP_PASSWORD
        ])
    
    def _get_recipients(self) -> List[str]:
        """获取收件人列表
        
        Returns:
            收件人邮箱列表
        """
        recipients = []
        
        if self.config.EMAIL_TO:
            if isinstance(self.config.EMAIL_TO, str):
                recipients = [email.strip() for email in self.config.EMAIL_TO.split(",")]
            elif isinstance(self.config.EMAIL_TO, list):
                recipients = self.config.EMAIL_TO
        
        return recipients

"""
邮件发送模块

提供邮件发送功能，包括：
- 发送复习提醒邮件
- HTML 格式邮件转换
- SMTP 连接测试
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from ...config.settings import AppConfig
import re


class EmailSender:
    """邮件发送器

    负责发送复习提醒邮件，支持纯文本和 HTML 两种格式。

    Attributes:
        config: 应用配置对象
    """

    def __init__(self, config: AppConfig):
        """初始化邮件发送器

        Args:
            config: 应用配置对象
        """
        self.config = config

    def send(self, content: Dict[str, str]):
        """发送邮件

        Args:
            content: 邮件内容字典，包含 subject 和 body

        Raises:
            ValueError: 邮件配置不完整时
            smtplib.SMTPException: 发送失败时
        """
        if not all([self.config.SMTP_USER, self.config.SMTP_PASSWORD, self.config.EMAIL_TO]):
            raise ValueError("邮件配置不完整")

        message = MIMEMultipart("alternative")
        message["Subject"] = content["subject"]
        message["From"] = self.config.EMAIL_FROM
        message["To"] = self.config.EMAIL_TO

        text_part = MIMEText(content["body"], "plain", "utf-8")
        message.attach(text_part)

        html_body = self._convert_to_html(content["body"])
        html_part = MIMEText(html_body, "html", "utf-8")
        message.attach(html_part)

        with smtplib.SMTP_SSL(self.config.SMTP_HOST, self.config.SMTP_PORT) as server:
            server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
            server.send_message(message)

    def _convert_to_html(self, text: str) -> str:
        """将纯文本转换为 HTML

        处理代码块、行内代码、分隔线等元素的转换。

        Args:
            text: 纯文本内容

        Returns:
            HTML 格式的邮件内容
        """
        html = text
        html = html.replace("\n\n", "</p><p>")
        html = f"<p>{html}</p>"
        html = re.sub(r"```([\s\S]*?)```", r"<pre><code>\1</code></pre>", html)
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
        html = re.sub(r"━+", "<hr>", html)
        return html

    def test_connection(self) -> bool:
        """测试 SMTP 连接

        验证邮件配置是否正确。

        Returns:
            连接是否成功
        """
        try:
            with smtplib.SMTP_SSL(self.config.SMTP_HOST, self.config.SMTP_PORT) as server:
                server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
            return True
        except Exception:
            return False

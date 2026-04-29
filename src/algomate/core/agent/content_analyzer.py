"""
内容分析器模块

提供内容的分析和处理功能，包括：
- 调用 AI 分析内容
- 提取代码片段
- 解析 Markdown 结构
"""

from typing import Any, List, Dict
import re
from .chat_client import ChatClient, ContentAnalysisResult
import json


class ContentAnalyzer:
    """内容分析器

    负责内容的智能分析和结构化处理。

    Attributes:
        chat_client: AI 对话客户端实例
    """

    def __init__(self, chat_client: ChatClient):
        """初始化分析器

        Args:
            chat_client: AI 对话客户端实例
        """
        self.chat_client = chat_client

    def analyze_content(self, content: str) -> ContentAnalysisResult:
        """分析内容

        调用 AI 模型分析内容，提取关键信息。

        Args:
            content: 内容字符串

        Returns:
            包含分析结果的 ContentAnalysisResult 对象
        """
        return self.chat_client.analyze_note(content)

    def extract_code_snippets(self, content: str) -> List[str]:
        """提取代码片段

        从内容中提取所有代码块和行内代码。

        Args:
            content: 内容字符串

        Returns:
            代码片段列表
        """
        code_pattern = r"```[\s\S]*?```|`[^`]+`"
        matches = re.findall(code_pattern, content)
        return matches

    async def process_content(self, content: str) -> ContentAnalysisResult:
        """处理内容

        分析内容并返回分析结果。

        Args:
            content: 内容字符串

        Returns:
            ContentAnalysisResult 分析结果对象
        """
        result = self.chat_client.analyze_note(content)
        return result

    def parse_markdown_structure(self, content: str) -> Dict[str, Any]:
        """解析 Markdown 结构

        将 Markdown 内容按标题分段，提取各部分内容。

        Args:
            content: Markdown 格式的内容

        Returns:
            字典，键为标题，值为对应的内容
        """
        sections = {}
        lines = content.split("\n")
        current_section = None
        current_content = []

        for line in lines:
            if line.startswith("#"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line.lstrip("#").strip()
                current_content = []
            else:
                if current_section is None:
                    current_section = "introduction"
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

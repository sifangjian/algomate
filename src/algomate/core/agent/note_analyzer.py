"""
笔记分析器模块

提供笔记内容的分析和处理功能，包括：
- 调用 AI 分析笔记
- 提取代码片段
- 解析 Markdown 结构
"""

from typing import Any, List
import re
from .chat_client import ChatClient, NoteAnalysisResult
from ...data.models import Note
from ...data.database import Database
import json


class NoteAnalyzer:
    """笔记分析器

    负责笔记内容的智能分析和结构化处理。

    Attributes:
        chat_client: AI 对话客户端实例
    """

    def __init__(self, chat_client: ChatClient):
        """初始化分析器

        Args:
            chat_client: AI 对话客户端实例
        """
        self.chat_client = chat_client

    def analyze_note(self, note_content: str) -> NoteAnalysisResult:
        """分析笔记内容

        调用 AI 模型分析笔记，提取关键信息。

        Args:
            note_content: 笔记内容

        Returns:
            包含分析结果的 NoteAnalysisResult 对象
        """
        return self.chat_client.analyze_note(note_content)

    def extract_code_snippets(self, content: str) -> List[str]:
        """提取代码片段

        从笔记内容中提取所有代码块和行内代码。

        Args:
            content: 笔记内容

        Returns:
            代码片段列表
        """
        code_pattern = r"```[\s\S]*?```|`[^`]+`"
        matches = re.findall(code_pattern, content)
        return matches

    async def process_note(self, note: Note, db: Database) -> Note:
        """处理笔记

        分析笔记内容并更新笔记属性。

        Args:
            note: 笔记对象
            db: 数据库实例

        Returns:
            更新后的笔记对象
        """
        session = db.get_session()
        try:
            result = self.chat_client.analyze_note(note.content)

            note.algorithm_type = result.algorithm_type
            note.difficulty = result.difficulty
            note.summary = result.summary

            tags = result.tags
            if isinstance(tags, list):
                note.tags = json.dumps(tags, ensure_ascii=False)
            else:
                note.tags = json.dumps([tags], ensure_ascii=False) if tags else "[]"

            if not note.summary and result.key_points:
                note.summary = "; ".join(result.key_points[:3])

            session.commit()
            session.refresh(note)
            return note
        finally:
            session.close()

    def parse_markdown_structure(self, content: str) -> Dict[str, Any]:
        """解析 Markdown 结构

        将 Markdown 内容按标题分段，提取各部分内容。

        Args:
            content: Markdown 格式的笔记内容

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

"""
题目生成器模块

提供智能出题功能，包括：
- 根据笔记生成练习题
- 根据薄弱点生成针对性练习题
- 将生成结果持久化到数据库
"""

from typing import List, Dict, Any
import random
from .chat_client import ChatClient
from ...data.models import Question
from ...data.database import Database
import json


class QuestionGenerator:
    """题目生成器

    负责根据笔记内容和薄弱点生成练习题。

    Attributes:
        chat_client: AI 对话客户端实例
        QUESTION_TYPES: 支持的题目类型列表
    """

    QUESTION_TYPES = ["选择题", "简答题", "代码题"]

    def __init__(self, chat_client: ChatClient):
        """初始化生成器

        Args:
            chat_client: AI 对话客户端实例
        """
        self.chat_client = chat_client

    def generate_for_note(
        self, note_content: str, count: int = 3
    ) -> List[Dict[str, Any]]:
        """根据笔记生成练习题

        随机选择题目类型，调用 AI 生成练习题。

        Args:
            note_content: 笔记内容
            count: 生成题目数量

        Returns:
            题目列表
        """
        selected_types = random.sample(self.QUESTION_TYPES, min(3, count))
        result = self.chat_client.generate_questions(note_content, selected_types, count)
        return result

    def generate_weak_point_questions(
        self, weak_topics: List[Dict[str, Any]], count: int = 5
    ) -> List[Dict[str, Any]]:
        """根据薄弱点生成练习题

        针对用户薄弱知识点生成专项练习。

        Args:
            weak_topics: 薄弱知识点列表
            count: 生成题目数量

        Returns:
            题目列表
        """
        questions = []
        for topic in weak_topics[:count]:
            prompt = f"""针对"{topic['name']}"这个薄弱知识点，生成一道高质量练习题。
            要求：
            - 题目类型：选择题或简答题
            - 难度：中等
            - 能有效检验用户是否真正掌握

            请返回JSON格式：
            - question_type: 题目类型
            - content: 题目内容
            - answer: 参考答案
            - explanation: 解析"""
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed:
                questions.append(parsed)
        return questions

    def create_questions_from_result(
        self, note_id: int, result: List[Dict[str, Any]], db: Database
    ) -> List[Question]:
        """将生成结果保存到数据库

        Args:
            note_id: 关联的笔记 ID
            result: 生成的题目列表
            db: 数据库实例

        Returns:
            创建的题目对象列表
        """
        session = db.get_session()
        created_questions = []
        try:
            for item in result:
                question = Question(
                    note_id=note_id,
                    question_type=item.get("question_type", "简答题"),
                    content=item.get("content", ""),
                    answer=item.get("answer", ""),
                    explanation=item.get("explanation", ""),
                )
                session.add(question)
                created_questions.append(question)
            session.commit()
            for q in created_questions:
                session.refresh(q)
            return created_questions
        finally:
            session.close()

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析 JSON 响应

        Args:
            response: 模型返回的文本

        Returns:
            解析后的字典对象
        """
        json_match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {}

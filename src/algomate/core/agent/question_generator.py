"""
题目生成器模块

提供智能出题功能，包括：
- 根据笔记生成练习题
- 根据薄弱点生成针对性练习题
- 将生成结果持久化到数据库
"""

import re
from typing import List, Dict, Any, Optional
import random
from .chat_client import ChatClient
from algomate.models import Question
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
        return self._convert_questions_to_dict(result)

    def generate_multiple_choice(
        self,
        note_content: str,
        difficulty: str = "中等",
        count: int = 1,
    ) -> List[Dict[str, Any]]:
        """生成选择题

        根据笔记内容生成高质量的选择题，包含4个选项。

        Args:
            note_content: 笔记内容
            difficulty: 难度等级（简单/中等/困难）
            count: 生成题目数量

        Returns:
            选择题列表，每道题包含选项
        """
        questions = []
        for _ in range(count):
            prompt = f"""根据以下算法笔记，生成一道高质量的选择题：

{note_content}

要求：
- 难度：{difficulty}
- 必须有4个选项（A、B、C、D）
- 只有一个正确答案
- 选项要有一定的干扰性

请返回JSON格式：
{{
    "question_type": "选择题",
    "content": "题目内容（包含选项A、B、C、D）",
    "answer": "正确答案（如：A）",
    "explanation": "解析"
}}"""
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed and "question_type" in parsed:
                parsed["options"] = self._extract_options(parsed.get("content", ""))
                questions.append(parsed)
        return questions

    def generate_short_answer(
        self,
        note_content: str,
        difficulty: str = "中等",
        count: int = 1,
    ) -> List[Dict[str, Any]]:
        """生成简答题

        根据笔记内容生成简答题，考查对概念和原理的理解。

        Args:
            note_content: 笔记内容
            difficulty: 难度等级（简单/中等/困难）
            count: 生成题目数量

        Returns:
            简答题列表
        """
        questions = []
        for _ in range(count):
            prompt = f"""根据以下算法笔记，生成一道高质量的简答题：

{note_content}

要求：
- 难度：{difficulty}
- 考查对算法概念、原理的理解
- 答案应该简洁但完整

请返回JSON格式：
{{
    "question_type": "简答题",
    "content": "题目内容",
    "answer": "参考答案要点",
    "explanation": "解析"
}}"""
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed and "question_type" in parsed:
                questions.append(parsed)
        return questions

    def generate_code_question(
        self,
        note_content: str,
        difficulty: str = "中等",
        count: int = 1,
    ) -> List[Dict[str, Any]]:
        """生成代码题

        根据笔记内容生成代码题，要求实现特定算法或解决编程问题。

        Args:
            note_content: 笔记内容
            difficulty: 难度等级（简单/中等/困难）
            count: 生成题目数量

        Returns:
            代码题列表
        """
        questions = []
        for _ in range(count):
            prompt = f"""根据以下算法笔记，生成一道高质量的代码题：

{note_content}

要求：
- 难度：{difficulty}
- 需要编写代码实现算法
- 给出输入输出示例

请返回JSON格式：
{{
    "question_type": "代码题",
    "content": "题目描述（包含函数签名、输入输出说明）",
    "answer": "参考代码实现",
    "explanation": "解题思路分析"
}}"""
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed and "question_type" in parsed:
                questions.append(parsed)
        return questions

    def generate_weak_point_questions(
        self,
        weak_topics: List[Dict[str, Any]],
        count: int = 5,
        question_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """根据薄弱点生成练习题

        针对用户薄弱知识点生成专项练习。

        Args:
            weak_topics: 薄弱知识点列表，每个元素包含 name（知识点名称）
            count: 生成题目数量
            question_types: 题目类型列表，默认包含选择题和简答题

        Returns:
            题目列表
        """
        if question_types is None:
            question_types = ["选择题", "简答题"]

        questions = []
        types_to_generate = question_types * (count // len(question_types) + 1)

        for i, topic in enumerate(weak_topics[:count]):
            question_type = types_to_generate[i]
            prompt = self._build_weak_point_prompt(topic, question_type)
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed and "question_type" in parsed:
                questions.append(parsed)

        return questions

    def _build_weak_point_prompt(
        self,
        topic: Dict[str, Any],
        question_type: str,
    ) -> str:
        """构建薄弱点题目的提示词

        Args:
            topic: 薄弱知识点字典
            question_type: 题目类型

        Returns:
            格式化的提示词
        """
        topic_name = topic.get("name", "")
        topic_context = topic.get("context", "")
        difficulty = topic.get("difficulty", "中等")

        base_prompt = f"""针对"{topic_name}"这个薄弱知识点，生成一道高质量练习题。

知识背景：{topic_context}
难度：{difficulty}
题目类型：{question_type}

"""

        if question_type == "选择题":
            base_prompt += """要求：
- 必须有4个选项（A、B、C、D）
- 只有一个正确答案
- 选项要有一定的干扰性

请返回JSON格式：
{
    "question_type": "选择题",
    "content": "题目内容（包含选项）",
    "answer": "正确答案",
    "explanation": "解析"
}"""
        elif question_type == "简答题":
            base_prompt += """要求：
- 考查对概念、原理的理解
- 答案应该简洁但完整

请返回JSON格式：
{
    "question_type": "简答题",
    "content": "题目内容",
    "answer": "参考答案要点",
    "explanation": "解析"
}"""
        elif question_type == "代码题":
            base_prompt += """要求：
- 需要编写代码实现
- 给出输入输出示例

请返回JSON格式：
{
    "question_type": "代码题",
    "content": "题目描述",
    "answer": "参考代码",
    "explanation": "解题思路"
}"""

        return base_prompt

    def _extract_options(self, content: str) -> Dict[str, str]:
        """从题目内容中提取选项

        Args:
            content: 题目内容

        Returns:
            选项字典，键为 A/B/C/D，值为选项内容
        """
        options = {}
        option_pattern = r'([A-D])[.、]\s*([^\n]+)'
        matches = re.findall(option_pattern, content)
        for letter, text in matches:
            options[letter] = text.strip()
        return options

    def _convert_questions_to_dict(
        self,
        questions: List[Any],
    ) -> List[Dict[str, Any]]:
        """将 Question 对象列表转换为字典列表

        Args:
            questions: Question 对象列表

        Returns:
            字典列表
        """
        result = []
        for q in questions:
            if hasattr(q, "__dict__"):
                result.append(q.__dict__)
            elif isinstance(q, dict):
                result.append(q)
        return result

    def create_questions_from_result(
        self, card_id: int, result: List[Dict[str, Any]], db: Database
    ) -> List[Question]:
        """将生成结果保存到数据库

        Args:
            card_id: 关联的卡牌 ID
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
                    card_id=card_id,
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
                parsed = json.loads(json_match.group())
                if isinstance(parsed, list):
                    if parsed:
                        return parsed[0]
                elif isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        return {}
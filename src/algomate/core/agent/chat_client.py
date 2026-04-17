"""
智谱 GLM API 客户端模块

封装与智谱 GLM-4 大模型的交互接口，提供：
- 通用对话功能
- 笔记分析功能
- 题目生成功能
- 答案评估功能

使用 requests 库发送 HTTP 请求，支持 JSON 格式的响应解析。
"""

import requests
from typing import Optional, List, Dict, Any
import json
import re


class ChatClient:
    """智谱 GLM API 客户端

    封装与智谱大模型的 API 调用，提供对话和特定任务接口。

    Attributes:
        api_key: 智谱 API 密钥
        model: 使用的模型名称
        base_url: API 基础 URL

    Example:
        client = ChatClient(api_key="your-api-key")
        response = client.chat([{"role": "user", "content": "你好"}])
    """

    def __init__(self, api_key: str, model: str = "glm-4"):
        """初始化客户端

        Args:
            api_key: 智谱 API 密钥
            model: 模型名称，默认为 glm-4
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """发送对话请求

        Args:
            messages: 对话消息列表，每条消息包含 role 和 content
            temperature: 生成温度参数，控制随机性

        Returns:
            模型生成的回复内容

        Raises:
            requests.HTTPError: 当 API 请求失败时
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def analyze_note(self, note_content: str) -> Dict[str, Any]:
        """分析算法笔记

        调用大模型分析笔记内容，提取关键信息。

        Args:
            note_content: 笔记内容（Markdown格式）

        Returns:
            包含以下字段的字典：
            - algorithm_type: 算法类型
            - key_points: 关键知识点列表
            - difficulty: 难度等级
            - tags: 标签列表
            - summary: 一句话总结
        """
        prompt = f"""请分析以下算法笔记，提取关键信息：
        {note_content}

        请以JSON格式返回，包含：
        - algorithm_type: 算法类型（如：动态规划、贪心、DFS等）
        - key_points: 关键知识点列表
        - difficulty: 难度等级（简单/中等/困难）
        - tags: 相关标签列表
        - summary: 一句话总结"""
        messages = [{"role": "user", "content": prompt}]
        result = self.chat(messages)
        return self._parse_json_response(result)

    def generate_questions(
        self, note_content: str, question_types: List[str], count: int = 3
    ) -> List[Dict[str, Any]]:
        """生成练习题

        根据笔记内容生成指定数量和类型的练习题。

        Args:
            note_content: 笔记内容
            question_types: 题目类型列表（选择题/简答题/代码题）
            count: 生成题目数量

        Returns:
            题目列表，每道题包含 question_type、content、answer、explanation
        """
        prompt = f"""根据以下算法笔记，生成{count}道练习题：
        {note_content}

        题目类型要求：{', '.join(question_types)}

        请为每道题包含：
        - question_type: 题目类型
        - content: 题目内容
        - answer: 参考答案
        - explanation: 解析"""
        messages = [{"role": "user", "content": prompt}]
        result = self.chat(messages)
        parsed = self._parse_json_response(result)
        if isinstance(parsed, list):
            return parsed
        return [parsed] if parsed else []

    def evaluate_answer(
        self, question: str, user_answer: str, correct_answer: str
    ) -> Dict[str, Any]:
        """评估用户答案

        分析用户答案与参考答案的差异，提供反馈。

        Args:
            question: 题目内容
            user_answer: 用户答案
            correct_answer: 参考答案

        Returns:
            包含以下字段的字典：
            - is_correct: 是否正确
            - feedback: 详细评价
            - improvement: 改进建议
        """
        prompt = f"""题目：{question}
        用户答案：{user_answer}
        参考答案：{correct_answer}

        请分析用户答案，给出JSON格式返回：
        - is_correct: 是否正确
        - feedback: 详细评价
        - improvement: 改进建议"""
        messages = [{"role": "user", "content": prompt}]
        result = self.chat(messages)
        return self._parse_json_response(result)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析 JSON 响应

        从模型返回的文本中提取 JSON 内容。

        Args:
            response: 模型返回的文本

        Returns:
            解析后的字典对象，若解析失败返回包含 raw 字段的字典
        """
        json_match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {"raw": response}

"""
试炼生成器模块

提供智能出题功能，包括：
- 根据心得生成试炼
- 根据薄弱点生成针对性试炼
- 将生成结果持久化到数据库
"""

import re
from typing import List, Dict, Any, Optional
import random
from .chat_client import ChatClient
from algomate.models import Question
from ...data.database import Database
import json


LEETCODE_FALLBACK_MAP = {
    "基础数据结构": {
        "title": "两数之和",
        "url": "https://leetcode.cn/problems/two-sum/",
        "difficulty": "easy",
        "description": "给定一个整数数组和一个目标值，找出数组中和为目标值的两个数"
    },
    "数组": {
        "title": "两数之和",
        "url": "https://leetcode.cn/problems/two-sum/",
        "difficulty": "easy",
        "description": "给定一个整数数组和一个目标值，找出数组中和为目标值的两个数"
    },
    "链表": {
        "title": "反转链表",
        "url": "https://leetcode.cn/problems/reverse-linked-list/",
        "difficulty": "easy",
        "description": "反转一个单链表"
    },
    "栈": {
        "title": "有效的括号",
        "url": "https://leetcode.cn/problems/valid-parentheses/",
        "difficulty": "easy",
        "description": "判断字符串中的括号是否有效匹配"
    },
    "队列": {
        "title": "用栈实现队列",
        "url": "https://leetcode.cn/problems/implement-queue-using-stacks/",
        "difficulty": "easy",
        "description": "使用栈实现队列的基本操作"
    },
    "哈希表": {
        "title": "两数之和",
        "url": "https://leetcode.cn/problems/two-sum/",
        "difficulty": "easy",
        "description": "使用哈希表高效查找目标值"
    },
    "二分查找": {
        "title": "二分查找",
        "url": "https://leetcode.cn/problems/binary-search/",
        "difficulty": "easy",
        "description": "在有序数组中使用二分查找定位目标值"
    },
    "递归": {
        "title": "爬楼梯",
        "url": "https://leetcode.cn/problems/climbing-stairs/",
        "difficulty": "easy",
        "description": "使用递归或动态规划计算爬楼梯的方法数"
    },
    "回溯": {
        "title": "全排列",
        "url": "https://leetcode.cn/problems/permutations/",
        "difficulty": "medium",
        "description": "给定不含重复数字的数组，返回所有可能的全排列"
    },
    "树遍历": {
        "title": "二叉树的中序遍历",
        "url": "https://leetcode.cn/problems/binary-tree-inorder-traversal/",
        "difficulty": "easy",
        "description": "返回二叉树的中序遍历结果"
    },
    "DFS": {
        "title": "岛屿数量",
        "url": "https://leetcode.cn/problems/number-of-islands/",
        "difficulty": "medium",
        "description": "使用深度优先搜索计算网格中岛屿的数量"
    },
    "BFS": {
        "title": "岛屿数量",
        "url": "https://leetcode.cn/problems/number-of-islands/",
        "difficulty": "medium",
        "description": "使用广度优先搜索计算网格中岛屿的数量"
    },
    "动态规划": {
        "title": "最长递增子序列",
        "url": "https://leetcode.cn/problems/longest-increasing-subsequence/",
        "difficulty": "medium",
        "description": "找到数组中最长递增子序列的长度"
    },
    "贪心算法": {
        "title": "跳跃游戏",
        "url": "https://leetcode.cn/problems/jump-game/",
        "difficulty": "medium",
        "description": "使用贪心策略判断能否到达数组末尾"
    },
    "分治策略": {
        "title": "排序数组",
        "url": "https://leetcode.cn/problems/sort-an-array/",
        "difficulty": "medium",
        "description": "使用分治法（归并排序）对数组排序"
    },
    "图论": {
        "title": "克隆图",
        "url": "https://leetcode.cn/problems/clone-graph/",
        "difficulty": "medium",
        "description": "深度拷贝一个无向图"
    },
    "堆": {
        "title": "数组中的第K个最大元素",
        "url": "https://leetcode.cn/problems/kth-largest-element-in-an-array/",
        "difficulty": "medium",
        "description": "使用堆找到数组中第K大的元素"
    },
    "排序算法": {
        "title": "排序数组",
        "url": "https://leetcode.cn/problems/sort-an-array/",
        "difficulty": "medium",
        "description": "实现一个排序算法对数组排序"
    },
    "双指针": {
        "title": "盛最多水的容器",
        "url": "https://leetcode.cn/problems/container-with-most-water/",
        "difficulty": "medium",
        "description": "使用双指针找到能盛最多水的容器"
    },
    "滑动窗口": {
        "title": "无重复字符的最长子串",
        "url": "https://leetcode.cn/problems/longest-substring-without-repeating-characters/",
        "difficulty": "medium",
        "description": "使用滑动窗口找到不含重复字符的最长子串"
    },
}


class QuestionGenerator:
    """试炼生成器

    负责根据心得内容和薄弱点生成试炼。

    Attributes:
        chat_client: AI 对话客户端实例
        QUESTION_TYPES: 支持的试炼类型列表
    """

    QUESTION_TYPES = ["选择题", "简答题", "LeetCode挑战"]

    def __init__(self, chat_client: ChatClient):
        """初始化生成器

        Args:
            chat_client: AI 对话客户端实例
        """
        self.chat_client = chat_client

    def generate_for_note(
        self, note_content: str, count: int = 3
    ) -> List[Dict[str, Any]]:
        """根据心得生成试炼

        随机选择试炼类型，调用 AI 生成试炼。

        Args:
            note_content: 心得内容
            count: 生成试炼数量

        Returns:
            试炼列表
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

        根据心得内容生成高质量的选择题，包含4个选项。

        Args:
            note_content: 心得内容
            difficulty: 难度等级（简单/中等/困难）
            count: 生成试炼数量

        Returns:
            选择题列表，每道题包含选项
        """
        questions = []
        for _ in range(count):
            prompt = f"""根据以下算法心得，生成一道高质量的选择题：

{note_content}

要求：
- 难度：{difficulty}
- 必须有4个选项（A、B、C、D）
- 只有一个正确答案
- 选项要有一定的干扰性

请返回JSON格式：
{{
    "question_type": "选择题",
    "content": "试炼内容（包含选项A、B、C、D）",
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

        根据心得内容生成简答题，考查对概念和原理的理解。

        Args:
            note_content: 心得内容
            difficulty: 难度等级（简单/中等/困难）
            count: 生成试炼数量

        Returns:
            简答题列表
        """
        questions = []
        for _ in range(count):
            prompt = f"""根据以下算法心得，生成一道高质量的简答题：

{note_content}

要求：
- 难度：{difficulty}
- 考查对算法概念、原理的理解
- 答案应该简洁但完整

请返回JSON格式：
{{
    "question_type": "简答题",
    "content": "试炼内容",
    "answer": "参考答案要点",
    "explanation": "解析"
}}"""
            messages = [{"role": "user", "content": prompt}]
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed and "question_type" in parsed:
                questions.append(parsed)
        return questions

    def generate_leetcode_challenge(
        self,
        note_content: str,
        difficulty: str = "medium",
        algorithm_type: str = "",
    ) -> Dict[str, Any]:
        """生成 LeetCode 挑战题

        先尝试用 AI 推荐一道 LeetCode 题目，若 AI 推荐失败或返回无效数据，
        则从 LEETCODE_FALLBACK_MAP 中查找匹配条目（先精确匹配 algorithm_type，
        再模糊匹配 note_content 中的关键词），若映射表也未找到则使用默认的"两数之和"。

        Args:
            note_content: 心得内容，用于 AI 推荐及模糊匹配回退
            difficulty: 难度等级（easy/medium/hard）
            algorithm_type: 算法类型，用于精确匹配回退

        Returns:
            包含 LeetCode 题目信息的字典，格式为：
            {
                "question_type": "LeetCode挑战",
                "content": 描述,
                "leetcode_title": 标题,
                "leetcode_url": URL,
                "leetcode_difficulty": 难度,
                "leetcode_description": 描述,
                "answer": "self_report",
                "explanation": ""
            }
        """
        prompt = f"""根据以下算法心得，推荐一道合适的LeetCode题目。

心得内容：
{note_content}

算法类型：{algorithm_type or '自动识别'}
难度：{difficulty}

要求：
- 题目必须与心得内容紧密相关
- 提供LeetCode中文站链接

请返回JSON格式：
{{
    "title": "LeetCode题目标题",
    "url": "https://leetcode.cn/problems/xxx/",
    "difficulty": "easy/medium/hard",
    "description": "题目描述摘要"
}}"""
        messages = [{"role": "user", "content": prompt}]
        try:
            result = self.chat_client.chat(messages)
            parsed = self._parse_json_response(result)
            if parsed and parsed.get("title") and parsed.get("url"):
                return {
                    "question_type": "LeetCode挑战",
                    "content": parsed.get("description", ""),
                    "leetcode_title": parsed["title"],
                    "leetcode_url": parsed["url"],
                    "leetcode_difficulty": parsed.get("difficulty", difficulty),
                    "leetcode_description": parsed.get("description", ""),
                    "answer": "self_report",
                    "explanation": "",
                }
        except Exception:
            pass

        return self._get_leetcode_fallback(note_content, algorithm_type)

    def _get_leetcode_fallback(
        self, note_content: str, algorithm_type: str = ""
    ) -> Dict[str, Any]:
        """从回退映射表中获取 LeetCode 题目

        查找策略：
        1. 精确匹配 algorithm_type
        2. 模糊匹配 note_content 中包含的映射表关键词
        3. 若均未命中，使用默认的"两数之和"

        Args:
            note_content: 心得内容，用于模糊匹配映射表中的算法类型关键词
            algorithm_type: 算法类型，用于精确匹配

        Returns:
            包含 LeetCode 题目信息的标准字典
        """
        fb = None

        # 策略1：精确匹配 algorithm_type
        if algorithm_type and algorithm_type in LEETCODE_FALLBACK_MAP:
            fb = LEETCODE_FALLBACK_MAP[algorithm_type]

        # 策略2：模糊匹配 note_content 中的关键词
        if fb is None and note_content:
            for key, val in LEETCODE_FALLBACK_MAP.items():
                if key in note_content:
                    fb = val
                    break

        # 策略3：默认回退到"两数之和"
        if fb is None:
            fb = LEETCODE_FALLBACK_MAP.get(
                "数组",
                {
                    "title": "两数之和",
                    "url": "https://leetcode.cn/problems/two-sum/",
                    "difficulty": "easy",
                    "description": "给定一个整数数组和一个目标值，找出数组中和为目标值的两个数",
                },
            )

        return {
            "question_type": "LeetCode挑战",
            "content": fb.get("description", ""),
            "leetcode_title": fb["title"],
            "leetcode_url": fb["url"],
            "leetcode_difficulty": fb["difficulty"],
            "leetcode_description": fb.get("description", ""),
            "answer": "self_report",
            "explanation": "",
        }

    def generate_weak_point_questions(
        self,
        weak_topics: List[Dict[str, Any]],
        count: int = 5,
        question_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """根据薄弱点生成试炼

        针对用户薄弱秘术生成专项试炼。

        Args:
            weak_topics: 薄弱秘术列表，每个元素包含 name（秘术名称）
            count: 生成试炼数量
            question_types: 试炼类型列表，默认包含选择题和简答题

        Returns:
            试炼列表
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
        """构建薄弱点试炼的提示词

        Args:
            topic: 薄弱秘术字典
            question_type: 试炼类型

        Returns:
            格式化的提示词
        """
        topic_name = topic.get("name", "")
        topic_context = topic.get("context", "")
        difficulty = topic.get("difficulty", "中等")

        base_prompt = f"""针对"{topic_name}"这个薄弱秘术，生成一道高质量试炼。

知识背景：{topic_context}
难度：{difficulty}
试炼类型：{question_type}

"""

        if question_type == "选择题":
            base_prompt += """要求：
- 必须有4个选项（A、B、C、D）
- 只有一个正确答案
- 选项要有一定的干扰性

请返回JSON格式：
{
    "question_type": "选择题",
    "content": "试炼内容（包含选项）",
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
    "content": "试炼内容",
    "answer": "参考答案要点",
    "explanation": "解析"
}"""
        elif question_type == "LeetCode挑战":
            base_prompt += """要求：
- 推荐一道LeetCode题目
- 提供LeetCode中文站链接

请返回JSON格式：
{
    "question_type": "LeetCode挑战",
    "content": "题目描述摘要",
    "answer": "解题思路要点",
    "explanation": "算法思路分析",
    "leetcode_url": "https://leetcode.cn/problems/xxx/",
    "leetcode_title": "LeetCode题目标题",
    "leetcode_difficulty": "Easy/Medium/Hard"
}"""

        return base_prompt

    def _extract_options(self, content: str) -> List[str]:
        options = {}
        option_pattern = r'([A-D])[.、]\s*([^\n]+)'
        matches = re.findall(option_pattern, content)
        for letter, text in matches:
            options[letter] = text.strip()
        return [options[k] for k in sorted(options.keys())]

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
            result: 生成的试炼列表
            db: 数据库实例

        Returns:
            创建的试炼对象列表
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
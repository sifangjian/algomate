"""
1.10 LeetCode挑战集成 单元测试

测试覆盖：
- LEETCODE_FALLBACK_MAP 覆盖全部33种算法类型，每种至少2道题目
- _get_leetcode_fallback 按难度匹配和已完成过滤逻辑
- generate_leetcode_challenge 去重逻辑
- AnswerRecord 新增 leetcode_url 字段
- get_completed_leetcode_urls 方法
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from algomate.core.agent.question_generator import (
    LEETCODE_FALLBACK_MAP,
    QuestionGenerator,
)
from algomate.config.algorithm_types import ALGORITHM_TYPES


class TestLeetCodeFallbackMapCoverage(unittest.TestCase):
    """测试 LEETCODE_FALLBACK_MAP 覆盖完整性"""

    def test_covers_all_algorithm_types(self):
        """映射表应覆盖全部33种算法类型"""
        for algo_type in ALGORITHM_TYPES:
            self.assertIn(
                algo_type,
                LEETCODE_FALLBACK_MAP,
                f"LEETCODE_FALLBACK_MAP 缺少算法类型: {algo_type}"
            )

    def test_each_type_has_at_least_two_problems(self):
        """每种算法类型至少有2道推荐题目"""
        for algo_type, problems in LEETCODE_FALLBACK_MAP.items():
            self.assertIsInstance(
                problems, list,
                f"{algo_type} 的值应为列表"
            )
            self.assertGreaterEqual(
                len(problems), 2,
                f"{algo_type} 至少应有2道题目，当前只有 {len(problems)} 道"
            )

    def test_each_problem_has_required_fields(self):
        """每道题目必须包含 title, url, difficulty, description 字段"""
        required_fields = {"title", "url", "difficulty", "description"}
        for algo_type, problems in LEETCODE_FALLBACK_MAP.items():
            for i, problem in enumerate(problems):
                missing = required_fields - set(problem.keys())
                self.assertFalse(
                    missing,
                    f"{algo_type} 第{i+1}道题目缺少字段: {missing}"
                )

    def test_each_problem_has_valid_difficulty(self):
        """每道题目的难度应为 easy/medium/hard"""
        valid_difficulties = {"easy", "medium", "hard"}
        for algo_type, problems in LEETCODE_FALLBACK_MAP.items():
            for i, problem in enumerate(problems):
                self.assertIn(
                    problem["difficulty"],
                    valid_difficulties,
                    f"{algo_type} 第{i+1}道题目难度无效: {problem['difficulty']}"
                )

    def test_each_problem_has_valid_url(self):
        """每道题目的URL应为LeetCode中文站链接"""
        for algo_type, problems in LEETCODE_FALLBACK_MAP.items():
            for i, problem in enumerate(problems):
                self.assertTrue(
                    problem["url"].startswith("https://leetcode.cn/problems/"),
                    f"{algo_type} 第{i+1}道题目URL格式无效: {problem['url']}"
                )

    def test_each_type_has_different_difficulties(self):
        """每种算法类型至少有2种不同难度的题目"""
        for algo_type, problems in LEETCODE_FALLBACK_MAP.items():
            difficulties = set(p["difficulty"] for p in problems)
            self.assertGreaterEqual(
                len(difficulties), 2,
                f"{algo_type} 应至少有2种不同难度，当前只有: {difficulties}"
            )


class TestGetLeetCodeFallback(unittest.TestCase):
    """测试 _get_leetcode_fallback 方法"""

    def setUp(self):
        self.generator = QuestionGenerator(chat_client=MagicMock())

    def test_exact_match_algorithm_type(self):
        """精确匹配算法类型应返回该类型的题目"""
        result = self.generator._get_leetcode_fallback(
            note_content="",
            algorithm_type="链表"
        )
        self.assertEqual(result["question_type"], "LeetCode挑战")
        self.assertTrue(
            result["leetcode_url"].startswith("https://leetcode.cn/problems/")
        )
        fb_problems = LEETCODE_FALLBACK_MAP["链表"]
        urls = [p["url"] for p in fb_problems]
        self.assertIn(result["leetcode_url"], urls)

    def test_fuzzy_match_note_content(self):
        """模糊匹配心得内容中的关键词"""
        result = self.generator._get_leetcode_fallback(
            note_content="今天学习了线性DP的相关知识",
            algorithm_type=""
        )
        self.assertEqual(result["question_type"], "LeetCode挑战")
        fb_problems = LEETCODE_FALLBACK_MAP["线性DP"]
        urls = [p["url"] for p in fb_problems]
        self.assertIn(result["leetcode_url"], urls)

    def test_default_fallback(self):
        """未匹配到任何类型时应使用默认回退"""
        result = self.generator._get_leetcode_fallback(
            note_content="一些无关内容",
            algorithm_type="不存在的类型"
        )
        self.assertEqual(result["question_type"], "LeetCode挑战")
        default_problems = LEETCODE_FALLBACK_MAP["数组与双指针"]
        urls = [p["url"] for p in default_problems]
        self.assertIn(result["leetcode_url"], urls)

    def test_filter_completed_urls(self):
        """应过滤已完成的题目URL"""
        fb_problems = LEETCODE_FALLBACK_MAP["链表"]
        completed_url = fb_problems[0]["url"]
        completed_urls = [completed_url]

        for _ in range(20):
            result = self.generator._get_leetcode_fallback(
                note_content="",
                algorithm_type="链表",
                completed_urls=completed_urls
            )
            self.assertNotEqual(
                result["leetcode_url"], completed_url,
                "已完成的题目不应被再次推荐"
            )

    def test_all_completed_falls_back_to_any(self):
        """所有题目都已完成时应从全部题目中随机选择（允许重复）"""
        fb_problems = LEETCODE_FALLBACK_MAP["栈与队列"]
        all_urls = [p["url"] for p in fb_problems]

        result = self.generator._get_leetcode_fallback(
            note_content="",
            algorithm_type="栈与队列",
            completed_urls=all_urls
        )
        self.assertEqual(result["question_type"], "LeetCode挑战")
        self.assertIn(result["leetcode_url"], all_urls)

    def test_difficulty_matching(self):
        """指定难度时应优先返回匹配难度的题目"""
        result = self.generator._get_leetcode_fallback(
            note_content="",
            algorithm_type="链表",
            difficulty="easy"
        )
        fb_problems = LEETCODE_FALLBACK_MAP["链表"]
        easy_problems = [p for p in fb_problems if p["difficulty"] == "easy"]
        if easy_problems:
            self.assertEqual(result["leetcode_difficulty"], "easy")

    def test_difficulty_fallback_when_no_match(self):
        """指定难度但无匹配题目时应返回任意题目"""
        result = self.generator._get_leetcode_fallback(
            note_content="",
            algorithm_type="递归",
            difficulty="hard"
        )
        self.assertEqual(result["question_type"], "LeetCode挑战")
        fb_problems = LEETCODE_FALLBACK_MAP["递归"]
        urls = [p["url"] for p in fb_problems]
        self.assertIn(result["leetcode_url"], urls)

    def test_completed_urls_and_difficulty_combined(self):
        """同时指定已完成URL和难度时应正确过滤和匹配"""
        fb_problems = LEETCODE_FALLBACK_MAP["哈希表"]
        easy_urls = [p["url"] for p in fb_problems if p["difficulty"] == "easy"]

        if len(easy_urls) > 0:
            completed_urls = [easy_urls[0]]
            result = self.generator._get_leetcode_fallback(
                note_content="",
                algorithm_type="哈希表",
                completed_urls=completed_urls,
                difficulty="easy"
            )
            remaining_easy = [p for p in fb_problems
                              if p["difficulty"] == "easy" and p["url"] not in completed_urls]
            if remaining_easy:
                self.assertEqual(result["leetcode_difficulty"], "easy")
                self.assertNotIn(result["leetcode_url"], completed_urls)


class TestGenerateLeetCodeChallenge(unittest.TestCase):
    """测试 generate_leetcode_challenge 方法"""

    def setUp(self):
        self.mock_client = MagicMock()
        self.generator = QuestionGenerator(chat_client=self.mock_client)

    def test_ai_returns_valid_result(self):
        """AI返回有效结果时应直接使用"""
        self.mock_client.chat.return_value = '''{
            "title": "测试题目",
            "url": "https://leetcode.cn/problems/test-problem/",
            "difficulty": "medium",
            "description": "测试描述"
        }'''

        result = self.generator.generate_leetcode_challenge(
            note_content="测试心得",
            difficulty="medium",
            algorithm_type="链表"
        )
        self.assertEqual(result["leetcode_title"], "测试题目")
        self.assertEqual(result["leetcode_url"], "https://leetcode.cn/problems/test-problem/")
        self.assertEqual(result["leetcode_difficulty"], "medium")

    def test_ai_returns_completed_url_falls_back(self):
        """AI返回已完成URL时应降级到回退映射"""
        completed_url = "https://leetcode.cn/problems/test-problem/"
        self.mock_client.chat.return_value = '''{
            "title": "测试题目",
            "url": "https://leetcode.cn/problems/test-problem/",
            "difficulty": "medium",
            "description": "测试描述"
        }'''

        result = self.generator.generate_leetcode_challenge(
            note_content="测试心得",
            difficulty="medium",
            algorithm_type="链表",
            completed_urls=[completed_url]
        )
        self.assertNotEqual(result["leetcode_url"], completed_url)
        fb_problems = LEETCODE_FALLBACK_MAP["链表"]
        urls = [p["url"] for p in fb_problems]
        self.assertIn(result["leetcode_url"], urls)

    def test_ai_failure_falls_back(self):
        """AI调用失败时应降级到回退映射"""
        self.mock_client.chat.side_effect = Exception("AI服务不可用")

        result = self.generator.generate_leetcode_challenge(
            note_content="测试心得",
            difficulty="medium",
            algorithm_type="线性DP"
        )
        self.assertEqual(result["question_type"], "LeetCode挑战")
        fb_problems = LEETCODE_FALLBACK_MAP["线性DP"]
        urls = [p["url"] for p in fb_problems]
        self.assertIn(result["leetcode_url"], urls)

    def test_ai_returns_invalid_json_falls_back(self):
        """AI返回无效JSON时应降级到回退映射"""
        self.mock_client.chat.return_value = "这不是有效的JSON"

        result = self.generator.generate_leetcode_challenge(
            note_content="测试心得",
            difficulty="easy",
            algorithm_type="数组与双指针"
        )
        self.assertEqual(result["question_type"], "LeetCode挑战")

    def test_completed_urls_passed_to_fallback(self):
        """completed_urls应正确传递到回退方法"""
        self.mock_client.chat.side_effect = Exception("AI不可用")
        fb_problems = LEETCODE_FALLBACK_MAP["哈希表"]
        completed_url = fb_problems[0]["url"]

        result = self.generator.generate_leetcode_challenge(
            note_content="测试心得",
            difficulty="medium",
            algorithm_type="哈希表",
            completed_urls=[completed_url]
        )
        self.assertNotEqual(result["leetcode_url"], completed_url)

    def test_default_completed_urls_is_empty(self):
        """不传completed_urls时应正常工作"""
        self.mock_client.chat.side_effect = Exception("AI不可用")

        result = self.generator.generate_leetcode_challenge(
            note_content="测试心得",
            difficulty="medium",
            algorithm_type="栈与队列"
        )
        self.assertEqual(result["question_type"], "LeetCode挑战")


class TestAnswerRecordLeetCodeUrl(unittest.TestCase):
    """测试 AnswerRecord leetcode_url 字段"""

    def test_model_has_leetcode_url_column(self):
        """AnswerRecord模型应包含leetcode_url字段"""
        from algomate.models.answer_records import AnswerRecord
        columns = {c.name for c in AnswerRecord.__table__.columns}
        self.assertIn("leetcode_url", columns)

    def test_create_schema_has_leetcode_url(self):
        """AnswerRecordCreate应包含leetcode_url字段"""
        from algomate.models.answer_records import AnswerRecordCreate
        fields = AnswerRecordCreate.model_fields
        self.assertIn("leetcode_url", fields)

    def test_response_schema_has_leetcode_url(self):
        """AnswerRecordResponse应包含leetcode_url字段"""
        from algomate.models.answer_records import AnswerRecordResponse
        fields = AnswerRecordResponse.model_fields
        self.assertIn("leetcode_url", fields)

    def test_create_schema_default_empty(self):
        """leetcode_url默认值应为空字符串"""
        from algomate.models.answer_records import AnswerRecordCreate
        record = AnswerRecordCreate(
            user_answer="test",
            is_correct=True
        )
        self.assertEqual(record.leetcode_url, "")


class TestCompletedLeetCodeUrlsAPI(unittest.TestCase):
    """测试已完成LeetCode URL查询"""

    def test_completed_leetcode_endpoint_exists(self):
        """completed-leetcode端点应存在"""
        from algomate.models.answer_records import router
        routes = [r.path for r in router.routes]
        self.assertTrue(
            any("completed-leetcode" in r for r in routes),
            f"completed-leetcode not found in routes: {routes}"
        )

    def test_completed_leetcode_method_is_get(self):
        """completed-leetcode端点应为GET方法"""
        from algomate.models.answer_records import router
        for route in router.routes:
            if hasattr(route, 'path') and 'completed-leetcode' in route.path:
                self.assertIn("GET", route.methods)
                return
        self.fail("未找到 completed-leetcode 路由")


if __name__ == "__main__":
    unittest.main()

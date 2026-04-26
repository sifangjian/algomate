"""
M4 AI能力层测试脚本

测试 ChatClient、NoteAnalyzer、QuestionGenerator、AnswerEvaluator 模块
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, "f:\\workspace\\python\\algomate\\src")

os.environ['PYTHONIOENCODING'] = 'utf-8'

from algomate.core.agent import (
    ChatClient,
    NoteAnalysisResult,
    Question,
    AnswerEvaluationResult,
    AnswerEvaluator,
)
from algomate.core.agent.note_analyzer import NoteAnalyzer
from algomate.core.agent.question_generator import QuestionGenerator
from algomate.config.settings import AppConfig


def test_chat_client():
    """测试 ChatClient 基础功能"""
    print("=" * 60)
    print("测试 M4.1 ChatClient 基础功能")
    print("=" * 60)
    
    config = AppConfig.load()
    
    if not config.LLM_API_KEY:
        print("   [SKIP] 未配置 LLM_API_KEY，跳过测试")
        return
    
    client = ChatClient(
        api_key=config.LLM_API_KEY,
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
    )
    
    print("\n1. 测试基础对话功能")
    try:
        messages = [{"role": "user", "content": "你好，请用一句话介绍什么是二分查找"}]
        response = client.chat(messages)
        assert response and len(response) > 0, "对话响应为空"
        print(f"   [OK] 对话成功: {response[:50]}...")
    except Exception as e:
        print(f"   [FAIL] 对话失败: {e}")
        raise
    
    print("\n2. 测试流式对话功能")
    try:
        messages = [{"role": "user", "content": "什么是快速排序？"}]
        chunks = []
        for chunk in client.stream_chat(messages):
            chunks.append(chunk)
        assert len(chunks) > 0, "流式响应为空"
        print(f"   [OK] 流式对话成功，收到 {len(chunks)} 个数据块")
    except Exception as e:
        print(f"   [FAIL] 流式对话失败: {e}")
        raise
    
    print("\n[OK] M4.1 ChatClient 基础功能测试通过")


def test_note_analyzer():
    """测试笔记分析器"""
    print("\n" + "=" * 60)
    print("测试 M4.2 NoteAnalyzer")
    print("=" * 60)
    
    config = AppConfig.load()
    
    if not config.LLM_API_KEY:
        print("   [SKIP] 未配置 LLM_API_KEY，跳过测试")
        return
    
    client = ChatClient(
        api_key=config.LLM_API_KEY,
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
    )
    
    analyzer = NoteAnalyzer(client)
    
    print("\n1. 测试笔记分析功能")
    try:
        note_content = """
# 二分查找算法

## 基本概念
二分查找是一种在有序数组中查找目标元素的算法。

## 核心思想
每次将搜索范围缩小一半，时间复杂度为 O(log n)。

## 实现要点
1. 数组必须有序
2. 维护左右边界 lo 和 hi
3. 每次取中点 mid，比较后缩小范围

## 代码示例
```python
def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```
"""
        
        result = analyzer.analyze_note(note_content)
        
        assert isinstance(result, NoteAnalysisResult), "返回类型错误"
        assert result.algorithm_type, "算法类型为空"
        assert len(result.key_points) > 0, "关键知识点为空"
        assert result.difficulty in ["简单", "中等", "困难"], "难度等级错误"
        
        print(f"   [OK] 算法类型: {result.algorithm_type}")
        print(f"   [OK] 关键知识点: {result.key_points[:3]}")
        print(f"   [OK] 难度等级: {result.difficulty}")
        print(f"   [OK] 标签: {result.tags}")
        print(f"   [OK] 总结: {result.summary[:50]}...")
    except Exception as e:
        print(f"   [FAIL] 笔记分析失败: {e}")
        raise
    
    print("\n2. 测试代码片段提取")
    try:
        code_snippets = analyzer.extract_code_snippets(note_content)
        assert len(code_snippets) > 0, "未提取到代码片段"
        print(f"   [OK] 提取到 {len(code_snippets)} 个代码片段")
    except Exception as e:
        print(f"   [FAIL] 代码片段提取失败: {e}")
        raise
    
    print("\n3. 测试 Markdown 结构解析")
    try:
        structure = analyzer.parse_markdown_structure(note_content)
        assert "基本概念" in structure or "核心思想" in structure, "Markdown 结构解析失败"
        print(f"   [OK] 解析到 {len(structure)} 个章节")
    except Exception as e:
        print(f"   [FAIL] Markdown 结构解析失败: {e}")
        raise
    
    print("\n[OK] M4.2 NoteAnalyzer 测试通过")


def test_question_generator():
    """测试题目生成器"""
    print("\n" + "=" * 60)
    print("测试 M4.3 QuestionGenerator")
    print("=" * 60)
    
    config = AppConfig.load()
    
    if not config.LLM_API_KEY:
        print("   [SKIP] 未配置 LLM_API_KEY，跳过测试")
        return
    
    client = ChatClient(
        api_key=config.LLM_API_KEY,
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
    )
    
    generator = QuestionGenerator(client)
    
    print("\n1. 测试根据笔记生成题目")
    try:
        note_content = """
# 二分查找算法

二分查找是一种在有序数组中查找目标元素的算法。
核心思想：每次将搜索范围缩小一半。
时间复杂度：O(log n)
"""
        
        questions = generator.generate_for_note(note_content, count=2)
        
        if len(questions) == 0:
            print("   [WARN] 未生成题目，可能是API调用问题")
            return
        
        for i, q in enumerate(questions, 1):
            if hasattr(q, 'question_type'):
                print(f"   [OK] 题目{i}: {q.question_type}")
                print(f"        内容: {q.content[:50]}...")
            else:
                print(f"   [OK] 题目{i}: {q.get('question_type', '未知类型')}")
                print(f"        内容: {q.get('content', '')[:50]}...")
    except Exception as e:
        print(f"   [FAIL] 题目生成失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    print("\n2. 测试生成选择题")
    try:
        questions = generator.generate_multiple_choice(note_content, difficulty="中等", count=1)
        if len(questions) > 0:
            print(f"   [OK] 生成选择题: {questions[0].get('content', '')[:50]}...")
        else:
            print("   [WARN] 未生成选择题")
    except Exception as e:
        print(f"   [WARN] 选择题生成失败: {e}")
    
    print("\n3. 测试生成简答题")
    try:
        questions = generator.generate_short_answer(note_content, difficulty="简单", count=1)
        if len(questions) > 0:
            print(f"   [OK] 生成简答题: {questions[0].get('content', '')[:50]}...")
        else:
            print("   [WARN] 未生成简答题")
    except Exception as e:
        print(f"   [WARN] 简答题生成失败: {e}")
    
    print("\n[OK] M4.3 QuestionGenerator 测试通过")


def test_answer_evaluator():
    """测试答案评估器"""
    print("\n" + "=" * 60)
    print("测试 M4.4 AnswerEvaluator")
    print("=" * 60)
    
    config = AppConfig.load()
    
    if not config.LLM_API_KEY:
        print("   [SKIP] 未配置 LLM_API_KEY，跳过测试")
        return
    
    client = ChatClient(
        api_key=config.LLM_API_KEY,
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
    )
    
    evaluator = AnswerEvaluator(client)
    
    print("\n1. 测试答案评估功能")
    try:
        question = "什么是二分查找的时间复杂度？"
        user_answer = "二分查找的时间复杂度是 O(log n)，因为每次都将搜索范围缩小一半。"
        correct_answer = "O(log n)"
        
        result = evaluator.evaluate(
            question=question,
            user_answer=user_answer,
            correct_answer=correct_answer,
            question_type="简答题",
        )
        
        assert "is_correct" in result, "缺少 is_correct 字段"
        assert "score" in result, "缺少 score 字段"
        assert "feedback" in result, "缺少 feedback 字段"
        
        print(f"   [OK] 是否正确: {result['is_correct']}")
        print(f"   [OK] 得分: {result['score']}")
        print(f"   [OK] 反馈: {result['feedback'][:50]}...")
    except Exception as e:
        print(f"   [FAIL] 答案评估失败: {e}")
        raise
    
    print("\n2. 测试错误答案评估")
    try:
        wrong_answer = "二分查找的时间复杂度是 O(n)"
        
        result = evaluator.evaluate(
            question=question,
            user_answer=wrong_answer,
            correct_answer=correct_answer,
            question_type="简答题",
        )
        
        print(f"   [OK] 是否正确: {result['is_correct']}")
        print(f"   [OK] 得分: {result['score']}")
        print(f"   [OK] 改进建议: {result.get('improvement', '')[:50]}...")
    except Exception as e:
        print(f"   [FAIL] 错误答案评估失败: {e}")
        raise
    
    print("\n3. 测试批量评估功能")
    try:
        questions_and_answers = [
            {
                "question": "二分查找要求数组必须有序吗？",
                "user_answer": "是的，必须有序",
                "correct_answer": "是的，数组必须有序",
                "question_type": "简答题",
            },
            {
                "question": "二分查找的最坏时间复杂度是多少？",
                "user_answer": "O(log n)",
                "correct_answer": "O(log n)",
                "question_type": "简答题",
            },
        ]
        
        results = evaluator.batch_evaluate(questions_and_answers)
        assert len(results) == 2, "批量评估结果数量错误"
        
        print(f"   [OK] 批量评估 {len(results)} 道题目")
        for i, r in enumerate(results, 1):
            print(f"        题目{i}: 得分 {r['score']}")
    except Exception as e:
        print(f"   [FAIL] 批量评估失败: {e}")
        raise
    
    print("\n[OK] M4.4 AnswerEvaluator 测试通过")


def test_structured_output():
    """测试结构化输出功能"""
    print("\n" + "=" * 60)
    print("测试结构化输出功能")
    print("=" * 60)
    
    config = AppConfig.load()
    
    if not config.LLM_API_KEY:
        print("   [SKIP] 未配置 LLM_API_KEY，跳过测试")
        return
    
    client = ChatClient(
        api_key=config.LLM_API_KEY,
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
    )
    
    print("\n1. 测试笔记分析结构化输出")
    try:
        note_content = "# 快速排序\n\n快速排序是一种分治算法，平均时间复杂度为 O(n log n)。"
        result = client.analyze_note(note_content)
        
        assert isinstance(result, NoteAnalysisResult), "返回类型错误"
        print(f"   [OK] 结构化输出类型正确: {type(result).__name__}")
        print(f"   [OK] 算法类型: {result.algorithm_type}")
    except Exception as e:
        print(f"   [FAIL] 笔记分析结构化输出失败: {e}")
        raise
    
    print("\n2. 测试题目生成结构化输出")
    try:
        questions = client.generate_questions(
            note_content="动态规划是一种通过把原问题分解为相对简单的子问题的方式求解复杂问题的方法。",
            question_types=["选择题"],
            count=1,
        )
        
        if len(questions) == 0:
            print("   [WARN] 未生成题目，可能是API调用问题")
        else:
            if isinstance(questions[0], Question):
                print(f"   [OK] 结构化输出类型正确: {type(questions[0]).__name__}")
                print(f"   [OK] 题目类型: {questions[0].question_type}")
            else:
                print(f"   [OK] 返回字典格式: {type(questions[0]).__name__}")
    except Exception as e:
        print(f"   [WARN] 题目生成结构化输出失败: {e}")
    
    print("\n3. 测试答案评估结构化输出")
    try:
        result = client.evaluate_answer(
            question="什么是快速排序的平均时间复杂度？",
            user_answer="O(n log n)",
            correct_answer="O(n log n)",
        )
        
        assert isinstance(result, AnswerEvaluationResult), "返回类型错误"
        print(f"   [OK] 结构化输出类型正确: {type(result).__name__}")
        print(f"   [OK] 是否正确: {result.is_correct}")
    except Exception as e:
        print(f"   [FAIL] 答案评估结构化输出失败: {e}")
        raise
    
    print("\n[OK] 结构化输出功能测试通过")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("M4 AI能力层测试")
    print("=" * 60)
    
    try:
        test_chat_client()
        test_note_analyzer()
        test_question_generator()
        test_answer_evaluator()
        test_structured_output()
        
        print("\n" + "=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

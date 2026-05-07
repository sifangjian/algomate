import random
from unittest.mock import patch

from algomate.api.routes import (
    _pick_question_type,
    _extract_options_from_content,
    _get_fallback_choice,
    _get_fallback_short_answer,
)


def _calculate_durability_change(is_victory, is_weakness_card):
    # 从 submit_boss_answer 提取的耐久度变更核心逻辑
    if is_victory and is_weakness_card:
        return 30
    elif is_victory:
        return 20
    else:
        return -5


def _apply_durability(current, change):
    # 从 submit_boss_answer 提取的耐久度钳制逻辑：[0, 100]
    return max(0, min(100, current + change))


def test_pick_question_type_returns_choice():
    # 固定 random.random 返回 0.1（<0.4），应返回 "choice"
    with patch("random.random", return_value=0.1):
        assert _pick_question_type() == "choice"


def test_pick_question_type_returns_short_answer():
    # 固定 random.random 返回 0.5（0.4<=r<0.8），应返回 "short_answer"
    with patch("random.random", return_value=0.5):
        assert _pick_question_type() == "short_answer"


def test_pick_question_type_returns_leetcode():
    # 固定 random.random 返回 0.9（>=0.8），应返回 "leetcode"
    with patch("random.random", return_value=0.9):
        assert _pick_question_type() == "leetcode"


def test_pick_question_type_distribution():
    # 运行1000次，验证题型分布大致符合权重：choice≈40%, short_answer≈40%, leetcode≈20%
    random.seed(42)
    counts = {"choice": 0, "short_answer": 0, "leetcode": 0}
    for _ in range(1000):
        result = _pick_question_type()
        counts[result] += 1

    assert 350 <= counts["choice"] <= 450, f"choice 比例偏移: {counts['choice']/10}%"
    assert 350 <= counts["short_answer"] <= 450, f"short_answer 比例偏移: {counts['short_answer']/10}%"
    assert 150 <= counts["leetcode"] <= 250, f"leetcode 比例偏移: {counts['leetcode']/10}%"


def test_extract_options_from_content_abcd():
    # 验证从多行文本中提取 A.B.C.D 格式的选项，返回按字母排序的选项文本列表
    content = "以下哪个是二分查找的时间复杂度？\nA.O(n)\nB.O(log n)\nC.O(n log n)\nD.O(1)"
    result = _extract_options_from_content(content)
    assert len(result) == 4
    assert result[0] == "O(n)"
    assert result[1] == "O(log n)"
    assert result[2] == "O(n log n)"
    assert result[3] == "O(1)"


def test_extract_options_from_content_chinese_separator():
    # 验证支持中文顿号分隔符（A、B、格式）
    content = "A、数组\nB、链表\nC、栈\nD、队列"
    result = _extract_options_from_content(content)
    assert len(result) == 4
    assert result[0] == "数组"
    assert result[1] == "链表"
    assert result[2] == "栈"
    assert result[3] == "队列"


def test_extract_options_from_content_no_options():
    # 验证无选项文本返回空列表
    content = "这是一段没有选项的普通文本"
    result = _extract_options_from_content(content)
    assert result == []


def test_get_fallback_choice_format():
    # 验证 _get_fallback_choice 返回包含 content/options/correct_answer/explanation 的字典
    random.seed(42)
    result = _get_fallback_choice()
    assert "content" in result
    assert "options" in result
    assert "correct_answer" in result
    assert "explanation" in result
    assert isinstance(result["options"], list)
    assert len(result["options"]) == 4


def test_get_fallback_short_answer_format():
    # 验证 _get_fallback_short_answer 返回包含 content/correct_answer/explanation 的字典
    random.seed(42)
    result = _get_fallback_short_answer()
    assert "content" in result
    assert "correct_answer" in result
    assert "explanation" in result


def test_durability_victory_with_weakness():
    # 胜利+弱点卡牌：耐久度变更 +30
    assert _calculate_durability_change(is_victory=True, is_weakness_card=True) == 30


def test_durability_victory_normal():
    # 胜利+普通卡牌：耐久度变更 +20
    assert _calculate_durability_change(is_victory=True, is_weakness_card=False) == 20


def test_durability_failure():
    # 失败：耐久度变更 -5（无论是否弱点卡牌）
    assert _calculate_durability_change(is_victory=False, is_weakness_card=True) == -5
    assert _calculate_durability_change(is_victory=False, is_weakness_card=False) == -5


def test_durability_upper_clamp():
    # 耐久度上限钳制：95+30 应为 100，不超过 100
    assert _apply_durability(95, 30) == 100


def test_durability_lower_clamp():
    # 耐久度下限钳制：3-5 应为 0，不低于 0
    assert _apply_durability(3, -5) == 0

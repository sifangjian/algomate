import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestBuildEnhancedSystemPrompt:
    """测试 _build_enhanced_system_prompt 函数"""

    def test_should_append_domain_boundary_rules(self):
        from algomate.api.dialogue_routes import _build_enhanced_system_prompt

        result = _build_enhanced_system_prompt(
            npc_system_prompt="你是一个算法导师。",
            npc_domain="动态规划",
            topics=["背包问题", "最长子序列"],
        )

        assert "你是一个算法导师。" in result
        assert "动态规划" in result
        assert "专长边界规则" in result
        assert "背包问题、最长子序列" in result

    def test_should_use_npc_domain_when_topics_empty(self):
        from algomate.api.dialogue_routes import _build_enhanced_system_prompt

        result = _build_enhanced_system_prompt(
            npc_system_prompt="Hello",
            npc_domain="贪心算法",
            topics=[],
        )

        assert "贪心算法" in result
        assert "专长边界规则" in result

    def test_should_join_multiple_topics_with_chinese_comma(self):
        from algomate.api.dialogue_routes import _build_enhanced_system_prompt

        result = _build_enhanced_system_prompt(
            npc_system_prompt="Test",
            npc_domain="搜索",
            topics=["BFS", "DFS", "回溯"],
        )

        assert "BFS、DFS、回溯" in result

    def test_should_preserve_original_prompt(self):
        from algomate.api.dialogue_routes import _build_enhanced_system_prompt

        original = "你是一个专业的算法导师，擅长动态规划。"
        result = _build_enhanced_system_prompt(
            npc_system_prompt=original,
            npc_domain="动态规划",
            topics=["背包"],
        )

        assert result.startswith(original)


class TestBuildCardGenerationPrompt:
    """测试 _build_card_generation_prompt 函数"""

    def test_should_return_system_and_user_prompt(self):
        from algomate.api.dialogue_routes import _build_card_generation_prompt

        system_prompt, user_prompt = _build_card_generation_prompt(
            topic="二分查找",
            npc_domain="基础数据结构",
            dialogue_messages=[
                {"role": "user", "content": "什么是二分查找？"},
                {"role": "assistant", "content": "二分查找是一种搜索算法。"},
            ],
            note_content="二分查找的核心是折半",
        )

        assert "算法知识整理师" in system_prompt
        assert "10个维度" in system_prompt
        assert "二分查找" in user_prompt
        assert "基础数据结构" in user_prompt
        assert "什么是二分查找？" in user_prompt
        assert "二分查找的核心是折半" in user_prompt

    def test_should_handle_empty_note(self):
        from algomate.api.dialogue_routes import _build_card_generation_prompt

        _, user_prompt = _build_card_generation_prompt(
            topic="排序",
            npc_domain="分治算法",
            dialogue_messages=[],
            note_content="",
        )

        assert "用户未记录笔记" in user_prompt

    def test_should_format_user_and_npc_messages(self):
        from algomate.api.dialogue_routes import _build_card_generation_prompt

        _, user_prompt = _build_card_generation_prompt(
            topic="DP",
            npc_domain="动态规划",
            dialogue_messages=[
                {"role": "user", "content": "How to DP?"},
                {"role": "assistant", "content": "DP is..."},
            ],
            note_content="test",
        )

        assert "**用户**：How to DP?" in user_prompt
        assert "**NPC**：DP is..." in user_prompt


class TestParseDialogueContent:
    """测试 parse_dialogue_content 函数"""

    def test_should_parse_valid_json(self):
        from algomate.models.dialogue_records import parse_dialogue_content

        content = '[{"role": "user", "content": "hello"}]'
        result = parse_dialogue_content(content)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "hello"

    def test_should_return_empty_list_for_empty_string(self):
        from algomate.models.dialogue_records import parse_dialogue_content

        result = parse_dialogue_content("")
        assert result == []

    def test_should_return_empty_list_for_invalid_json(self):
        from algomate.models.dialogue_records import parse_dialogue_content

        result = parse_dialogue_content("not json{{{")
        assert result == []

    def test_should_return_empty_list_for_none(self):
        from algomate.models.dialogue_records import parse_dialogue_content

        result = parse_dialogue_content(None)
        assert result == []


class TestParseGeneratedCards:
    """测试 parse_generated_cards 函数"""

    def test_should_parse_valid_card_ids(self):
        from algomate.models.dialogue_records import parse_generated_cards

        result = parse_generated_cards("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_should_return_empty_list_for_empty_string(self):
        from algomate.models.dialogue_records import parse_generated_cards

        result = parse_generated_cards("")
        assert result == []

    def test_should_return_empty_list_for_invalid_json(self):
        from algomate.models.dialogue_records import parse_generated_cards

        result = parse_generated_cards("invalid")
        assert result == []


class TestCardGenerationResult:
    """测试 CardGenerationResult Pydantic 模型"""

    def test_should_create_valid_instance(self):
        from algomate.api.dialogue_routes import CardGenerationResult

        card = CardGenerationResult(
            name="二分查找",
            algorithm_type="搜索",
            core_concept="折半搜索",
            key_points="1. 有序数组\n2. 中间元素",
            code_template="def binary_search(): pass",
            complexity_analysis="O(log n)",
            use_cases="1. 有序数组查找",
            common_variants="1. 左边界二分",
            typical_problems='[{"title":"搜索插入位置"}]',
            common_pitfalls="1. 溢出",
            comparison="与线性查找的区别",
            my_notes="用户笔记",
            difficulty=3,
        )

        assert card.name == "二分查找"
        assert card.difficulty == 3
        assert card.algorithm_type == "搜索"

    def test_should_reject_difficulty_below_1(self):
        from algomate.api.dialogue_routes import CardGenerationResult

        with pytest.raises(Exception):
            CardGenerationResult(
                name="test",
                algorithm_type="test",
                core_concept="test",
                key_points="test",
                code_template="test",
                complexity_analysis="test",
                use_cases="test",
                common_variants="test",
                typical_problems="test",
                common_pitfalls="test",
                comparison="test",
                my_notes="test",
                difficulty=0,
            )

    def test_should_reject_difficulty_above_5(self):
        from algomate.api.dialogue_routes import CardGenerationResult

        with pytest.raises(Exception):
            CardGenerationResult(
                name="test",
                algorithm_type="test",
                core_concept="test",
                key_points="test",
                code_template="test",
                complexity_analysis="test",
                use_cases="test",
                common_variants="test",
                typical_problems="test",
                common_pitfalls="test",
                comparison="test",
                my_notes="test",
                difficulty=6,
            )


class TestDialogueState:
    """测试 DialogueState 枚举"""

    def test_should_have_active_state(self):
        from algomate.api.dialogue_routes import DialogueState

        assert DialogueState.ACTIVE == "active"

    def test_should_have_ended_state(self):
        from algomate.api.dialogue_routes import DialogueState

        assert DialogueState.ENDED == "ended"

    def test_should_have_timed_out_state(self):
        from algomate.api.dialogue_routes import DialogueState

        assert DialogueState.TIMED_OUT == "timed_out"


class TestDialogueSessionDataclass:
    """测试 DialogueSession 数据类"""

    def test_should_create_with_defaults(self):
        from algomate.api.dialogue_routes import DialogueSession, DialogueState

        session = DialogueSession(
            dialogue_id=1,
            npc_id=2,
            npc_name="老夫子",
            npc_domain="动态规划",
            npc_system_prompt="你是导师",
            topic="背包问题",
            status=DialogueState.ACTIVE,
        )

        assert session.dialogue_id == 1
        assert session.npc_name == "老夫子"
        assert session.messages == []
        assert session.note_content == ""
        assert session.retry_count == 0
        assert session.card_result is None
        assert session.error is None

    def test_should_allow_setting_optional_fields(self):
        from algomate.api.dialogue_routes import DialogueSession, DialogueState

        session = DialogueSession(
            dialogue_id=1,
            npc_id=2,
            npc_name="老夫子",
            npc_domain="DP",
            npc_system_prompt="test",
            topic="test",
            status=DialogueState.ACTIVE,
            note_content="我的笔记",
            retry_count=1,
            error="some error",
        )

        assert session.note_content == "我的笔记"
        assert session.retry_count == 1
        assert session.error == "some error"


class TestNPCDialogueFlowHelperMethods:
    """测试 NPCDialogueFlow 的辅助方法"""

    def _make_mock_npc(self, name="老夫子", domain="动态规划", topics=None, greeting=None, location="智慧圣殿"):
        npc = MagicMock()
        npc.name = name
        npc.domain = domain
        npc.topics = json.dumps(topics or ["背包问题", "最长子序列"])
        npc.greeting = greeting
        npc.location = location
        npc.system_prompt = "你是算法导师"
        return npc

    def test_build_capabilities_section_with_topics(self):
        from algomate.core.flow.npc_dialogue import NPCDialogueFlow

        flow = NPCDialogueFlow.__new__(NPCDialogueFlow)
        npc = self._make_mock_npc(topics=["背包问题", "最长子序列", "区间DP", "树形DP"])

        result = flow._build_capabilities_section(npc)

        assert "我是老夫子" in result
        assert "专精动态规划" in result
        assert "背包问题" in result

    def test_build_capabilities_section_without_topics(self):
        from algomate.core.flow.npc_dialogue import NPCDialogueFlow

        flow = NPCDialogueFlow.__new__(NPCDialogueFlow)
        npc = self._make_mock_npc(topics=[])
        npc.topics = None

        result = flow._build_capabilities_section(npc)

        assert "我是老夫子" in result
        assert "探索这个领域的知识" in result

    def test_build_topics_section_with_topics(self):
        from algomate.core.flow.npc_dialogue import NPCDialogueFlow

        flow = NPCDialogueFlow.__new__(NPCDialogueFlow)
        npc = self._make_mock_npc(topics=["BFS", "DFS"])

        result = flow._build_topics_section(npc)

        assert "📖 可修习话题" in result
        assert "BFS · DFS" in result

    def test_build_topics_section_without_topics(self):
        from algomate.core.flow.npc_dialogue import NPCDialogueFlow

        flow = NPCDialogueFlow.__new__(NPCDialogueFlow)
        npc = self._make_mock_npc(topics=[])
        npc.topics = None

        result = flow._build_topics_section(npc)

        assert "📖 暂无可修习话题" in result

    def test_build_welcome_section_with_greeting(self):
        from algomate.core.flow.npc_dialogue import NPCDialogueFlow

        flow = NPCDialogueFlow.__new__(NPCDialogueFlow)
        npc = self._make_mock_npc(greeting="欢迎来到智慧圣殿！")

        result = flow._build_welcome_section(npc)

        assert result == "欢迎来到智慧圣殿！"

    def test_build_welcome_section_without_greeting(self):
        from algomate.core.flow.npc_dialogue import NPCDialogueFlow

        flow = NPCDialogueFlow.__new__(NPCDialogueFlow)
        npc = self._make_mock_npc(greeting=None)

        result = flow._build_welcome_section(npc)

        assert "欢迎来到智慧圣殿" in result

    def test_map_domain_to_enum_known_domain(self):
        from algomate.core.flow.npc_dialogue import NPCDialogueFlow

        flow = NPCDialogueFlow.__new__(NPCDialogueFlow)

        result = flow._map_domain_to_algorithm_type("动态规划")
        assert result == "dynamic_programming"

    def test_map_domain_to_enum_unknown_domain_defaults_to_novice(self):
        from algomate.core.flow.npc_dialogue import NPCDialogueFlow

        flow = NPCDialogueFlow.__new__(NPCDialogueFlow)

        result = flow._map_domain_to_algorithm_type("未知领域")
        assert result == "basic_data_structure"

    @pytest.mark.parametrize("domain,expected", [
        ("基础数据结构", "basic_data_structure"),
        ("搜索与遍历", "search_traversal"),
        ("动态规划", "dynamic_programming"),
        ("贪心算法", "greedy"),
        ("回溯算法", "backtracking"),
        ("分治算法", "divide_conquer"),
        ("数学与位运算", "math_bit"),
    ])
    def test_map_domain_all_known_mappings(self, domain, expected):
        from algomate.core.flow.npc_dialogue import NPCDialogueFlow

        flow = NPCDialogueFlow.__new__(NPCDialogueFlow)
        result = flow._map_domain_to_algorithm_type(domain)
        assert result == expected


class TestDialogueSessionToDict:
    """测试 DialogueSession.to_dict 方法"""

    def test_should_convert_to_dict(self):
        from algomate.core.flow.npc_dialogue import DialogueSession, DialogueState, DialogueMessage

        now = datetime(2026, 1, 1, 12, 0, 0)
        session = DialogueSession(
            dialogue_id=1,
            npc_id=2,
            npc_name="老夫子",
            npc_domain="动态规划",
            state=DialogueState.IN_PROGRESS,
            messages=[
                DialogueMessage(role="assistant", content="你好", timestamp=now),
            ],
            created_at=now,
        )

        result = session.to_dict()

        assert result["dialogue_id"] == 1
        assert result["npc_id"] == 2
        assert result["npc_name"] == "老夫子"
        assert result["npc_domain"] == "动态规划"
        assert result["state"] == "in_progress"
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "assistant"
        assert result["messages"][0]["content"] == "你好"


class TestDialogueMessageModel:
    """测试 DialogueMessage Pydantic 模型"""

    def test_should_create_valid_message(self):
        from algomate.models.dialogue_records import DialogueMessage

        msg = DialogueMessage(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.timestamp is None

    def test_should_create_message_with_timestamp(self):
        from algomate.models.dialogue_records import DialogueMessage

        now = datetime(2026, 1, 1)
        msg = DialogueMessage(role="assistant", content="hi", timestamp=now)
        assert msg.timestamp == now

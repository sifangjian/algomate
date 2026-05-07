import json
import pytest
from unittest.mock import patch, MagicMock

from algomate.api.hall_routes import (
    _parse_json_field,
    RECOMMENDED_LEARNING_PATH,
    VALID_ALGORITHM_TYPES,
    DEFAULT_NPCS,
    init_default_npcs_v1,
)


class TestParseJsonField:
    """_parse_json_field 函数测试"""

    def test_should_parse_valid_json_array(self):
        """正向测试：合法 JSON 数组字符串应返回对应列表"""
        result = _parse_json_field('["数组与双指针", "链表"]')
        assert result == ["数组与双指针", "链表"]

    def test_should_return_empty_list_for_empty_string(self):
        """边界值测试：空字符串应返回空列表"""
        result = _parse_json_field("")
        assert result == []

    def test_should_return_empty_list_for_none(self):
        """边界值测试：None 应返回空列表"""
        result = _parse_json_field(None)
        assert result == []

    def test_should_return_empty_list_for_invalid_json(self):
        """异常测试：无效 JSON 应返回空列表"""
        result = _parse_json_field("not json")
        assert result == []

    def test_should_return_empty_list_for_json_object(self):
        """异常测试：JSON 对象（非数组）应返回空列表"""
        result = _parse_json_field('{"key": "value"}')
        assert result == []

    def test_should_parse_json_with_chinese(self):
        """正向测试：含中文的 JSON 应正确解析"""
        result = _parse_json_field('["贪心选择", "区间问题"]')
        assert result == ["贪心选择", "区间问题"]


class TestRecommendedLearningPath:
    """RECOMMENDED_LEARNING_PATH 常量测试"""

    def test_should_have_8_steps(self):
        """学习路径应包含 8 个步骤"""
        assert len(RECOMMENDED_LEARNING_PATH) == 8

    def test_first_step_should_be_laofuzi(self):
        """第一步应为老夫子（基础入门）"""
        first = RECOMMENDED_LEARNING_PATH[0]
        assert first["npc_name"] == "老夫子"
        assert first["algorithm_type"] == "basic_data_structure"
        assert first["stage"] == "基础入门"

    def test_last_step_should_be_zhizhe(self):
        """最后一步应为圣殿智者（动态规划）"""
        last = RECOMMENDED_LEARNING_PATH[-1]
        assert last["npc_name"] == "圣殿智者"
        assert last["algorithm_type"] == "dynamic_programming"

    def test_each_step_has_required_fields(self):
        """每个步骤应包含 order/npc_name/algorithm_type/stage/goal"""
        for step in RECOMMENDED_LEARNING_PATH:
            assert "order" in step
            assert "npc_name" in step
            assert "algorithm_type" in step
            assert "stage" in step
            assert "goal" in step

    def test_orders_should_be_sequential(self):
        """步骤顺序应为 1-8 连续递增"""
        orders = [step["order"] for step in RECOMMENDED_LEARNING_PATH]
        assert orders == [1, 2, 3, 4, 5, 6, 7, 8]


class TestValidAlgorithmTypes:
    """VALID_ALGORITHM_TYPES 常量测试"""

    def test_should_contain_8_types(self):
        """应有 8 种算法类型"""
        assert len(VALID_ALGORITHM_TYPES) == 8

    def test_should_contain_basic_data_structure(self):
        """应包含 basic_data_structure"""
        assert "basic_data_structure" in VALID_ALGORITHM_TYPES

    def test_should_contain_dynamic_programming(self):
        """应包含 dynamic_programming"""
        assert "dynamic_programming" in VALID_ALGORITHM_TYPES

    def test_should_not_contain_invalid_type(self):
        """不应包含无效类型"""
        assert "invalid_type" not in VALID_ALGORITHM_TYPES


class TestDefaultNpcs:
    """DEFAULT_NPCS 常量测试"""

    def test_should_have_8_npcs(self):
        """应有 8 个默认 NPC"""
        assert len(DEFAULT_NPCS) == 8

    def test_each_npc_has_required_fields(self):
        """每个 NPC 应包含 name/title/algorithm_type/specialties/avatar/description/topics"""
        for npc in DEFAULT_NPCS:
            assert "name" in npc
            assert "title" in npc
            assert "algorithm_type" in npc
            assert "specialties" in npc
            assert "avatar" in npc
            assert "description" in npc
            assert "topics" in npc

    def test_laofuzi_specialties(self):
        """老夫子专长应为数组与双指针、链表、哈希表"""
        laofuzi = DEFAULT_NPCS[0]
        assert laofuzi["name"] == "老夫子"
        assert laofuzi["specialties"] == ["数组与双指针", "链表", "哈希表"]
        assert laofuzi["algorithm_type"] == "basic_data_structure"

    def test_zhizhe_specialties(self):
        """圣殿智者专长应为线性DP、背包问题、子序列DP"""
        zhizhe = DEFAULT_NPCS[-1]
        assert zhizhe["name"] == "圣殿智者"
        assert zhizhe["specialties"] == ["线性DP", "背包问题", "子序列DP"]

    def test_algorithm_types_match_learning_path(self):
        """所有 NPC 的 algorithm_type 应在学习路径中出现"""
        path_types = {step["algorithm_type"] for step in RECOMMENDED_LEARNING_PATH}
        npc_types = {npc["algorithm_type"] for npc in DEFAULT_NPCS}
        assert npc_types == path_types


class TestInitDefaultNpcsV1:
    """init_default_npcs_v1 函数测试"""

    @patch("algomate.api.hall_routes.Database")
    def test_should_create_npcs_when_db_empty(self, mock_db_cls):
        """正向测试：数据库为空时应创建 8 个 NPC"""
        mock_db = MagicMock()
        mock_db_cls.get_instance.return_value = mock_db
        mock_session = MagicMock()
        mock_db.get_session.return_value = mock_session
        mock_session.query(NPC).count.return_value = 0

        init_default_npcs_v1()

        assert mock_session.add.call_count == 8
        mock_session.commit.assert_called_once()

    @patch("algomate.api.hall_routes.Database")
    def test_should_update_existing_npcs(self, mock_db_cls):
        """正向测试：数据库已有 NPC 时应更新字段"""
        mock_db = MagicMock()
        mock_db_cls.get_instance.return_value = mock_db
        mock_session = MagicMock()
        mock_db.get_session.return_value = mock_session
        mock_session.query(NPC).count.return_value = 8

        mock_existing = MagicMock()
        mock_existing.system_prompt = "existing"
        mock_existing.greeting = "existing greeting"
        mock_session.query(NPC).filter.return_value.first.return_value = mock_existing

        init_default_npcs_v1()

        mock_session.commit.assert_called_once()

    @patch("algomate.api.hall_routes.Database")
    def test_should_rollback_on_error(self, mock_db_cls):
        """异常测试：出错时应回滚"""
        mock_db = MagicMock()
        mock_db_cls.get_instance.return_value = mock_db
        mock_session = MagicMock()
        mock_db.get_session.return_value = mock_session
        mock_session.query(NPC).count.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            init_default_npcs_v1()

        mock_session.rollback.assert_called_once()


from algomate.models.npcs import NPC


class TestNpcModel:
    """NPC ORM 模型测试"""

    def test_should_have_new_fields(self):
        """NPC 模型应包含 title/algorithm_type/specialties/description 字段"""
        assert hasattr(NPC, 'title')
        assert hasattr(NPC, 'algorithm_type')
        assert hasattr(NPC, 'specialties')
        assert hasattr(NPC, 'description')

    def test_should_have_backward_compat_fields(self):
        """NPC 模型应保留 domain/location 用于向后兼容"""
        assert hasattr(NPC, 'domain')
        assert hasattr(NPC, 'location')

    def test_should_have_required_fields(self):
        """NPC 模型应包含基础字段"""
        assert hasattr(NPC, 'id')
        assert hasattr(NPC, 'name')
        assert hasattr(NPC, 'avatar')
        assert hasattr(NPC, 'system_prompt')
        assert hasattr(NPC, 'greeting')
        assert hasattr(NPC, 'topics')

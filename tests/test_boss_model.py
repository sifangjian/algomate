import pytest
from pydantic import ValidationError

from algomate.models.bosses import Difficulty, BossCreate, BossUpdate, BossResponse, Boss


def test_difficulty_enum_values():
    # 验证 Difficulty 枚举包含 easy/medium/hard 三个值，且枚举值为小写字符串
    assert Difficulty.EASY.value == "easy"
    assert Difficulty.MEDIUM.value == "medium"
    assert Difficulty.HARD.value == "hard"
    assert len(Difficulty) == 3


def test_boss_create_valid_data():
    # 验证合法数据能通过 BossCreate 校验，字段值与输入一致
    boss = BossCreate(
        name="数组守卫",
        difficulty=Difficulty.EASY,
        weakness_type="basic_data_structure",
        npc_id=1,
        description="新手森林的守门人",
    )
    assert boss.name == "数组守卫"
    assert boss.difficulty == Difficulty.EASY
    assert boss.weakness_type == "basic_data_structure"
    assert boss.npc_id == 1
    assert boss.description == "新手森林的守门人"


def test_boss_create_empty_name_fails():
    # 验证 name 为空字符串时 BossCreate 校验失败（min_length=1）
    with pytest.raises(ValidationError) as exc_info:
        BossCreate(
            name="",
            difficulty=Difficulty.EASY,
            weakness_type="basic_data_structure",
            npc_id=1,
            description="描述",
        )
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("name",)


def test_boss_create_weakness_type_too_long_fails():
    # 验证 weakness_type 超过30字符时 BossCreate 校验失败（max_length=30）
    with pytest.raises(ValidationError) as exc_info:
        BossCreate(
            name="测试Boss",
            difficulty=Difficulty.EASY,
            weakness_type="a" * 31,
            npc_id=1,
            description="描述",
        )
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("weakness_type",)


def test_boss_update_all_fields_optional():
    # 验证 BossUpdate 所有字段均为可选，无参数构造时各字段为 None
    update = BossUpdate()
    assert update.name is None
    assert update.difficulty is None
    assert update.weakness_type is None
    assert update.npc_id is None
    assert update.description is None


def test_boss_update_partial_fields():
    # 验证 BossUpdate 可只传入部分字段，其余保持 None
    update = BossUpdate(name="新名称", difficulty=Difficulty.HARD)
    assert update.name == "新名称"
    assert update.difficulty == Difficulty.HARD
    assert update.weakness_type is None
    assert update.npc_id is None
    assert update.description is None


def test_boss_response_from_attributes():
    # 验证 BossResponse 能通过 from_attributes 从 SQLAlchemy Boss 模型实例正确转换
    boss = Boss(
        id=1,
        name="数组守卫",
        difficulty="easy",
        weakness_type="basic_data_structure",
        npc_id=1,
        description="新手森林的守门人",
    )
    response = BossResponse.model_validate(boss, from_attributes=True)
    assert response.id == 1
    assert response.name == "数组守卫"
    assert response.difficulty == "easy"
    assert response.weakness_type == "basic_data_structure"
    assert response.npc_id == 1
    assert response.description == "新手森林的守门人"

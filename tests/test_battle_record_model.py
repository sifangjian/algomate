from algomate.models.battle_records import BattleRecord


def test_battle_record_default_status():
    # 验证 BattleRecord 的 status 列默认值为 'in_progress'
    assert BattleRecord.status.default.arg == 'in_progress'


def test_battle_record_default_durability_change():
    # 验证 BattleRecord 的 durability_change 列默认值为 0
    assert BattleRecord.durability_change.default.arg == 0


def test_battle_record_default_is_weakness_card():
    # 验证 BattleRecord 的 is_weakness_card 列默认值为 False
    assert BattleRecord.is_weakness_card.default.arg is False

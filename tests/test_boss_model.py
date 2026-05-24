from algomate.models.bosses import Boss


def test_boss_model_creation():
    boss = Boss(
        id=1,
        name="数组守卫",
        difficulty="easy",
        weakness_type="basic_data_structure",
        npc_id=1,
        description="新手森林的守门人",
    )
    assert boss.name == "数组守卫"
    assert boss.difficulty == "easy"
    assert boss.weakness_type == "basic_data_structure"
    assert boss.npc_id == 1
    assert boss.description == "新手森林的守门人"

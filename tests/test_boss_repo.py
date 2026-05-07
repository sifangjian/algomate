from algomate.data.repositories.boss_repo import BossRepository
from algomate.models.bosses import Boss


def test_get_all_returns_all_bosses(test_db, db_session, sample_npc):
    # 验证 get_all 返回数据库中所有 Boss 记录，数量和名称与插入数据一致
    boss1 = Boss(
        name="Boss1", difficulty="easy",
        weakness_type="type_a", npc_id=sample_npc.id, description="desc1",
    )
    boss2 = Boss(
        name="Boss2", difficulty="hard",
        weakness_type="type_b", npc_id=sample_npc.id, description="desc2",
    )
    db_session.add(boss1)
    db_session.add(boss2)
    db_session.commit()

    repo = BossRepository(test_db)
    result = repo.get_all()
    assert len(result) == 2
    names = [b.name for b in result]
    assert "Boss1" in names
    assert "Boss2" in names


def test_get_by_id_exists(test_db, db_session, sample_npc):
    # 验证 get_by_id 在记录存在时返回对应的 Boss 对象，字段值正确
    boss = Boss(
        name="BossX", difficulty="medium",
        weakness_type="type_c", npc_id=sample_npc.id, description="desc",
    )
    db_session.add(boss)
    db_session.commit()
    db_session.refresh(boss)

    repo = BossRepository(test_db)
    result = repo.get_by_id(boss.id)
    assert result is not None
    assert result.id == boss.id
    assert result.name == "BossX"


def test_get_by_id_not_exists(test_db):
    # 验证 get_by_id 在记录不存在时返回 None
    repo = BossRepository(test_db)
    result = repo.get_by_id(99999)
    assert result is None


def test_get_by_npc_id(test_db, db_session, sample_npc):
    # 验证 get_by_npc_id 按 npc_id 筛选，只返回匹配的 Boss 列表
    boss1 = Boss(
        name="Boss1", difficulty="easy",
        weakness_type="type_a", npc_id=sample_npc.id, description="desc1",
    )
    boss2 = Boss(
        name="Boss2", difficulty="hard",
        weakness_type="type_b", npc_id=sample_npc.id + 100, description="desc2",
    )
    db_session.add(boss1)
    db_session.add(boss2)
    db_session.commit()

    repo = BossRepository(test_db)
    result = repo.get_by_npc_id(sample_npc.id)
    assert len(result) == 1
    assert result[0].name == "Boss1"


def test_get_by_weakness_type(test_db, db_session, sample_npc):
    # 验证 get_by_weakness_type 按弱点类型筛选，只返回匹配的 Boss 列表
    boss1 = Boss(
        name="Boss1", difficulty="easy",
        weakness_type="dynamic_programming", npc_id=sample_npc.id, description="desc1",
    )
    boss2 = Boss(
        name="Boss2", difficulty="hard",
        weakness_type="greedy", npc_id=sample_npc.id, description="desc2",
    )
    db_session.add(boss1)
    db_session.add(boss2)
    db_session.commit()

    repo = BossRepository(test_db)
    result = repo.get_by_weakness_type("dynamic_programming")
    assert len(result) == 1
    assert result[0].name == "Boss1"

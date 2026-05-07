from algomate.data.repositories.battle_record_repo import BattleRecordRepository


def test_create_record(test_db, sample_boss, sample_card):
    # 验证 create 创建战斗记录后 status 为 'in_progress'，字段值与输入一致
    repo = BattleRecordRepository(test_db)
    record = repo.create(
        boss_id=sample_boss.id,
        card_id=sample_card.id,
        question_type="choice",
        is_weakness_card=True,
    )
    assert record is not None
    assert record.id is not None
    assert record.boss_id == sample_boss.id
    assert record.card_id == sample_card.id
    assert record.question_type == "choice"
    assert record.is_weakness_card is True
    assert record.status == "in_progress"


def test_get_by_id_exists(test_db, sample_boss, sample_card):
    # 验证 get_by_id 在记录存在时返回对应的 BattleRecord
    repo = BattleRecordRepository(test_db)
    created = repo.create(
        boss_id=sample_boss.id,
        card_id=sample_card.id,
        question_type="short_answer",
        is_weakness_card=False,
    )
    result = repo.get_by_id(created.id)
    assert result is not None
    assert result.id == created.id
    assert result.question_type == "short_answer"


def test_get_by_id_not_exists(test_db):
    # 验证 get_by_id 在记录不存在时返回 None
    repo = BattleRecordRepository(test_db)
    result = repo.get_by_id(99999)
    assert result is None


def test_get_active_by_card(test_db, sample_boss, sample_card):
    # 验证 get_active_by_card 返回指定卡牌下 status='in_progress' 的战斗记录
    repo = BattleRecordRepository(test_db)
    repo.create(
        boss_id=sample_boss.id,
        card_id=sample_card.id,
        question_type="choice",
        is_weakness_card=True,
    )
    repo.create(
        boss_id=sample_boss.id,
        card_id=sample_card.id,
        question_type="short_answer",
        is_weakness_card=False,
    )

    active = repo.get_active_by_card(sample_card.id)
    assert len(active) == 2
    for record in active:
        assert record.card_id == sample_card.id
        assert record.status == "in_progress"


def test_update_result_completes_record(test_db, sample_boss, sample_card):
    # 验证 update_result 将记录状态更新为 'completed'，并写入胜利、答案等字段
    repo = BattleRecordRepository(test_db)
    created = repo.create(
        boss_id=sample_boss.id,
        card_id=sample_card.id,
        question_type="choice",
        is_weakness_card=True,
    )

    updated = repo.update_result(
        record_id=created.id,
        is_victory=True,
        answer="B",
        score=100,
        durability_change=30,
        explanation="正确答案",
    )
    assert updated is not None
    assert updated.status == "completed"
    assert updated.is_victory is True
    assert updated.answer == "B"
    assert updated.score == 100
    assert updated.durability_change == 30
    assert updated.explanation == "正确答案"
    assert updated.completed_at is not None


def test_update_result_not_exists(test_db):
    # 验证 update_result 在记录不存在时返回 None
    repo = BattleRecordRepository(test_db)
    result = repo.update_result(
        record_id=99999,
        is_victory=False,
        answer="A",
        score=0,
        durability_change=-5,
    )
    assert result is None

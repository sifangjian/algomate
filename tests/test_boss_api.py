from unittest.mock import patch, MagicMock

from algomate.models.bosses import Boss
from algomate.models.cards import Card
from algomate.models.npcs import NPC
from algomate.data.database import Database


def _setup_test_data(test_db):
    session = test_db.get_session()
    npc = NPC(
        name="老夫子",
        title="基础数据结构导师",
        algorithm_type="basic_data_structure",
        specialties='["数组与双指针"]',
        avatar="laofuzi",
        description="基础数据结构的导师",
        system_prompt="你是老夫子",
        greeting="欢迎",
        topics='["数组与双指针"]',
    )
    session.add(npc)
    session.commit()
    session.refresh(npc)
    npc_id = npc.id

    boss = Boss(
        name="数组守卫",
        difficulty="easy",
        weakness_type="basic_data_structure",
        npc_id=npc_id,
        description="新手森林的守门人",
    )
    session.add(boss)
    session.commit()
    session.refresh(boss)
    boss_id = boss.id

    weakness_card = Card(
        name="数组双指针卡",
        algorithm_type="basic_data_structure",
        durability=80,
        npc_id=npc_id,
        topic="数组与双指针",
        core_concept="双指针技巧",
    )
    other_card = Card(
        name="动态规划卡",
        algorithm_type="dynamic_programming",
        durability=60,
        npc_id=npc_id,
        topic="动态规划",
        core_concept="DP思想",
    )
    session.add_all([weakness_card, other_card])
    session.commit()
    session.refresh(weakness_card)
    session.refresh(other_card)
    weakness_card_id = weakness_card.id
    other_card_id = other_card.id
    session.close()

    return npc_id, boss_id, weakness_card_id, other_card_id


def test_get_bosses(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    with patch.object(Database, 'get_instance', return_value=test_db):
        response = client.get("/api/v1/bosses")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "bosses" in data["data"]
    assert len(data["data"]["bosses"]) == 1
    boss_data = data["data"]["bosses"][0]
    assert boss_data["name"] == "数组守卫"
    assert boss_data["difficulty"] == "easy"
    assert boss_data["weakness_type"] == "basic_data_structure"
    assert boss_data["has_weakness_card"] is True
    assert boss_data["weakness_card_count"] == 1


def test_get_bosses_filter_difficulty(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    session = test_db.get_session()
    hard_boss = Boss(
        name="DP圣殿守卫",
        difficulty="hard",
        weakness_type="dynamic_programming",
        npc_id=npc_id,
        description="守护DP圣殿",
    )
    session.add(hard_boss)
    session.commit()
    session.close()

    with patch.object(Database, 'get_instance', return_value=test_db):
        response = client.get("/api/v1/bosses?difficulty=easy")

    assert response.status_code == 200
    data = response.json()
    bosses = data["data"]["bosses"]
    assert len(bosses) == 1
    assert bosses[0]["difficulty"] == "easy"

    with patch.object(Database, 'get_instance', return_value=test_db):
        response = client.get("/api/v1/bosses?difficulty=hard")

    assert response.status_code == 200
    data = response.json()
    bosses = data["data"]["bosses"]
    assert len(bosses) == 1
    assert bosses[0]["difficulty"] == "hard"


def test_get_boss_detail(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    with patch.object(Database, 'get_instance', return_value=test_db):
        response = client.get(f"/api/v1/bosses/{boss_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["name"] == "数组守卫"
    assert data["data"]["difficulty"] == "easy"
    assert data["data"]["weakness_type"] == "basic_data_structure"
    assert data["data"]["npc_id"] == npc_id
    assert len(data["data"]["weakness_cards"]) == 1
    assert data["data"]["weakness_cards"][0]["is_weakness"] is True
    assert len(data["data"]["other_cards"]) == 1
    assert data["data"]["other_cards"][0]["is_weakness"] is False
    assert data["data"]["has_weakness_card"] is True


def test_get_boss_detail_not_found(client, test_db):
    with patch.object(Database, 'get_instance', return_value=test_db):
        response = client.get("/api/v1/bosses/99999")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 40403
    assert "Boss不存在" in data["message"]


def test_challenge_boss(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    mock_generator = MagicMock()
    mock_generator.generate_multiple_choice.return_value = [
        {
            "content": "以下哪个是二分查找的时间复杂度？",
            "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
            "answer": "B",
            "explanation": "二分查找每次将搜索范围减半",
        }
    ]

    with patch.object(Database, 'get_instance', return_value=test_db), \
         patch('algomate.core.agent.question_generator.QuestionGenerator', return_value=mock_generator), \
         patch('algomate.api.v1.bosses._pick_question_type', return_value='choice'):
        response = client.post(
            f"/api/v1/bosses/{boss_id}/challenge",
            json={"card_id": weakness_card_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "battle_id" in data["data"]
    assert data["data"]["question_type"] == "choice"
    assert data["data"]["is_weakness_card"] is True
    assert "question" in data["data"]
    assert "content" in data["data"]["question"]
    assert "options" in data["data"]["question"]


def test_challenge_boss_no_card(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    with patch.object(Database, 'get_instance', return_value=test_db):
        response = client.post(
            f"/api/v1/bosses/{boss_id}/challenge",
            json={"card_id": 99999},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 40404


def test_submit_choice_answer(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    mock_generator = MagicMock()
    mock_generator.generate_multiple_choice.return_value = [
        {
            "content": "以下哪个是二分查找的时间复杂度？",
            "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
            "answer": "B",
            "explanation": "二分查找每次将搜索范围减半",
        }
    ]

    with patch.object(Database, 'get_instance', return_value=test_db), \
         patch('algomate.core.agent.question_generator.QuestionGenerator', return_value=mock_generator), \
         patch('algomate.api.v1.bosses._pick_question_type', return_value='choice'):
        challenge_resp = client.post(
            f"/api/v1/bosses/{boss_id}/challenge",
            json={"card_id": weakness_card_id},
        )

    battle_id = challenge_resp.json()["data"]["battle_id"]

    with patch.object(Database, 'get_instance', return_value=test_db):
        submit_resp = client.post(
            f"/api/v1/bosses/{boss_id}/submit",
            json={
                "battle_id": battle_id,
                "answer": "B",
                "question_type": "choice",
            },
        )

    assert submit_resp.status_code == 200
    data = submit_resp.json()
    assert data["code"] == 200
    assert data["data"]["is_victory"] is True
    assert data["data"]["durability_change"] == 30
    assert data["data"]["is_weakness_card"] is True
    assert data["data"]["correct_answer"] == "B"
    guide = data["data"]["guide"]
    continue_action = next(
        (a for a in guide["available_actions"] if a["action"] == "continue_challenge"),
        None,
    )
    assert continue_action is not None
    assert continue_action["available"] is True
    go_review_action = next(
        (a for a in guide["available_actions"] if a["action"] == "go_review"),
        None,
    )
    assert go_review_action is not None
    assert go_review_action["available"] is True


def test_submit_victory_guide_contains_continue_challenge_and_go_review(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    mock_generator = MagicMock()
    mock_generator.generate_multiple_choice.return_value = [
        {
            "content": "以下哪个是二分查找的时间复杂度？",
            "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
            "answer": "B",
            "explanation": "二分查找每次将搜索范围减半",
        }
    ]

    with patch.object(Database, 'get_instance', return_value=test_db), \
         patch('algomate.core.agent.question_generator.QuestionGenerator', return_value=mock_generator), \
         patch('algomate.api.v1.bosses._pick_question_type', return_value='choice'):
        challenge_resp = client.post(
            f"/api/v1/bosses/{boss_id}/challenge",
            json={"card_id": weakness_card_id},
        )

    battle_id = challenge_resp.json()["data"]["battle_id"]

    with patch.object(Database, 'get_instance', return_value=test_db):
        submit_resp = client.post(
            f"/api/v1/bosses/{boss_id}/submit",
            json={
                "battle_id": battle_id,
                "answer": "B",
                "question_type": "choice",
            },
        )

    data = submit_resp.json()["data"]
    assert data["is_victory"] is True
    guide = data["guide"]
    assert "available_actions" in guide
    assert "message" in guide
    actions = guide["available_actions"]
    action_names = [a["action"] for a in actions]
    assert "continue_challenge" in action_names
    assert "go_review" in action_names
    continue_action = next(a for a in actions if a["action"] == "continue_challenge")
    assert continue_action["label"] == "继续挑战"
    assert continue_action["target_path"] == "/boss/battle"
    assert continue_action["available"] is True
    go_review_action = next(a for a in actions if a["action"] == "go_review")
    assert go_review_action["label"] == "去修炼巩固"
    assert go_review_action["target_path"] == "/daily-review"
    assert "成功" in guide["message"]


def test_submit_defeat_guide_contains_go_review_and_go_dialogue(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    mock_generator = MagicMock()
    mock_generator.generate_multiple_choice.return_value = [
        {
            "content": "以下哪个是二分查找的时间复杂度？",
            "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
            "answer": "B",
            "explanation": "二分查找每次将搜索范围减半",
        }
    ]

    with patch.object(Database, 'get_instance', return_value=test_db), \
         patch('algomate.core.agent.question_generator.QuestionGenerator', return_value=mock_generator), \
         patch('algomate.api.v1.bosses._pick_question_type', return_value='choice'):
        challenge_resp = client.post(
            f"/api/v1/bosses/{boss_id}/challenge",
            json={"card_id": weakness_card_id},
        )

    battle_id = challenge_resp.json()["data"]["battle_id"]

    with patch.object(Database, 'get_instance', return_value=test_db):
        submit_resp = client.post(
            f"/api/v1/bosses/{boss_id}/submit",
            json={
                "battle_id": battle_id,
                "answer": "A",
                "question_type": "choice",
            },
        )

    data = submit_resp.json()["data"]
    assert data["is_victory"] is False
    guide = data["guide"]
    assert "available_actions" in guide
    assert "message" in guide
    actions = guide["available_actions"]
    action_names = [a["action"] for a in actions]
    assert "go_review" in action_names
    assert "go_dialogue" in action_names
    go_review_action = next(a for a in actions if a["action"] == "go_review")
    assert go_review_action["label"] == "去修炼巩固"
    assert go_review_action["target_path"] == "/review"
    go_dialogue_action = next(a for a in actions if a["action"] == "go_dialogue")
    assert go_dialogue_action["label"] == "去重新修习"
    assert go_dialogue_action["target_path"] == "/"
    assert go_dialogue_action["params"]["npc_id"] == npc_id
    assert "失败" in guide["message"] or "巩固" in guide["message"]


def test_submit_short_answer(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    mock_generator = MagicMock()
    mock_generator.generate_short_answer.return_value = [
        {
            "content": "请简述动态规划的核心思想",
            "answer": "将复杂问题分解为重叠子问题",
            "explanation": "动态规划通过记忆化避免重复计算",
        }
    ]

    mock_evaluator = MagicMock()
    mock_evaluator.evaluate.return_value = {
        "score": 80,
        "feedback": "回答较好",
        "improvement": "可以更详细",
        "explanation": "动态规划的核心是重叠子问题和最优子结构",
    }

    with patch.object(Database, 'get_instance', return_value=test_db), \
         patch('algomate.core.agent.question_generator.QuestionGenerator', return_value=mock_generator), \
         patch('algomate.api.v1.bosses._pick_question_type', return_value='short_answer'):
        challenge_resp = client.post(
            f"/api/v1/bosses/{boss_id}/challenge",
            json={"card_id": weakness_card_id},
        )

    battle_id = challenge_resp.json()["data"]["battle_id"]

    with patch.object(Database, 'get_instance', return_value=test_db), \
         patch('algomate.core.agent.answer_evaluator.AnswerEvaluator', return_value=mock_evaluator):
        submit_resp = client.post(
            f"/api/v1/bosses/{boss_id}/submit",
            json={
                "battle_id": battle_id,
                "answer": "将问题分解为子问题",
                "question_type": "short_answer",
            },
        )

    assert submit_resp.status_code == 200
    data = submit_resp.json()
    assert data["code"] == 200
    assert data["data"]["is_victory"] is True
    assert data["data"]["score"] == 80
    assert data["data"]["feedback"] == "回答较好"


def test_submit_leetcode(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    mock_generator = MagicMock()
    mock_generator.generate_leetcode_challenge.return_value = {
        "content": "请在LeetCode上完成两数之和",
        "leetcode_url": "https://leetcode.cn/problems/two-sum/",
        "leetcode_title": "两数之和",
        "leetcode_difficulty": "easy",
        "explanation": "使用哈希表优化",
    }

    with patch.object(Database, 'get_instance', return_value=test_db), \
         patch('algomate.core.agent.question_generator.QuestionGenerator', return_value=mock_generator), \
         patch('algomate.api.v1.bosses._pick_question_type', return_value='leetcode'):
        challenge_resp = client.post(
            f"/api/v1/bosses/{boss_id}/challenge",
            json={"card_id": weakness_card_id},
        )

    battle_id = challenge_resp.json()["data"]["battle_id"]

    with patch.object(Database, 'get_instance', return_value=test_db):
        submit_resp = client.post(
            f"/api/v1/bosses/{boss_id}/submit",
            json={
                "battle_id": battle_id,
                "answer": "已解决",
                "question_type": "leetcode",
                "is_solved": True,
            },
        )

    assert submit_resp.status_code == 200
    data = submit_resp.json()
    assert data["code"] == 200
    assert data["data"]["is_victory"] is True
    assert data["data"]["durability_change"] == 30
    assert data["data"]["correct_answer"] is None


def test_submit_victory_no_available_boss_removes_continue_challenge(client, test_db):
    npc_id, boss_id, weakness_card_id, other_card_id = _setup_test_data(test_db)

    mock_generator = MagicMock()
    mock_generator.generate_multiple_choice.return_value = [
        {
            "content": "以下哪个是二分查找的时间复杂度？",
            "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
            "answer": "B",
            "explanation": "二分查找每次将搜索范围减半",
        }
    ]

    with patch.object(Database, 'get_instance', return_value=test_db), \
         patch('algomate.core.agent.question_generator.QuestionGenerator', return_value=mock_generator), \
         patch('algomate.api.v1.bosses._pick_question_type', return_value='choice'):
        challenge_resp = client.post(
            f"/api/v1/bosses/{boss_id}/challenge",
            json={"card_id": weakness_card_id},
        )

    battle_id = challenge_resp.json()["data"]["battle_id"]

    with patch.object(Database, 'get_instance', return_value=test_db), \
         patch('algomate.api.v1.bosses._has_available_bosses', return_value=False):
        submit_resp = client.post(
            f"/api/v1/bosses/{boss_id}/submit",
            json={
                "battle_id": battle_id,
                "answer": "B",
                "question_type": "choice",
            },
        )

    data = submit_resp.json()["data"]
    assert data["is_victory"] is True
    guide = data["guide"]
    continue_action = next(
        (a for a in guide["available_actions"] if a["action"] == "continue_challenge"),
        None,
    )
    assert continue_action is not None
    assert continue_action["available"] is False

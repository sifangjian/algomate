from unittest.mock import patch, MagicMock


MOCK_CHOICE_QUESTION = [
    {
        "content": "以下哪个是二分查找的时间复杂度？",
        "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
        "answer": "B",
        "explanation": "二分查找每次将搜索范围减半，时间复杂度为O(log n)",
    }
]

MOCK_SHORT_ANSWER_QUESTION = [
    {
        "content": "请简述动态规划的核心思想",
        "answer": "将复杂问题分解为重叠子问题，通过存储子问题的解避免重复计算",
        "explanation": "动态规划通过记忆化或制表法，将指数级问题降为多项式级",
    }
]

MOCK_LEETCODE_CHALLENGE = {
    "question_type": "LeetCode挑战",
    "content": "给定一个整数数组和一个目标值，找出数组中和为目标值的两个数",
    "leetcode_title": "两数之和",
    "leetcode_url": "https://leetcode.cn/problems/two-sum/",
    "leetcode_difficulty": "easy",
    "leetcode_description": "两数之和",
    "answer": "self_report",
    "explanation": "",
}

MOCK_EVALUATE_RESULT = {
    "is_correct": True,
    "score": 85,
    "feedback": "回答较为完整，涵盖了核心思想",
    "correct_answer": "将复杂问题分解为重叠子问题",
    "explanation": "参考答案要点：将复杂问题分解为重叠子问题",
    "improvement": "可以进一步说明最优子结构性质",
}


def _mock_question_generator():
    generator = MagicMock()
    generator.generate_multiple_choice.return_value = MOCK_CHOICE_QUESTION
    generator.generate_short_answer.return_value = MOCK_SHORT_ANSWER_QUESTION
    generator.generate_leetcode_challenge.return_value = MOCK_LEETCODE_CHALLENGE
    return generator


def _mock_answer_evaluator(db=None):
    evaluator = MagicMock()
    evaluator.evaluate.return_value = MOCK_EVALUATE_RESULT
    return evaluator


QG_PATCH = "algomate.core.agent.question_generator.QuestionGenerator"
AE_PATCH = "algomate.core.agent.answer_evaluator.AnswerEvaluator"
PICK_TYPE_PATCH = "algomate.api.v1.bosses._pick_question_type"


class TestGetBosses:
    def test_returns_boss_list_with_has_any_card_true(self, test_app):
        resp = test_app.get("/api/v1/bosses")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert "bosses" in body["data"]
        assert "has_any_card" in body["data"]
        assert body["data"]["has_any_card"] is True
        bosses = body["data"]["bosses"]
        assert len(bosses) >= 1
        boss = bosses[0]
        assert "id" in boss
        assert "name" in boss
        assert "difficulty" in boss
        assert "weakness_type" in boss
        assert "description" in boss
        assert "has_weakness_card" in boss
        assert "weakness_card_count" in boss

    def test_filter_by_difficulty_returns_matching_bosses(self, test_app):
        resp = test_app.get("/api/v1/bosses?difficulty=easy")
        assert resp.status_code == 200
        body = resp.json()
        bosses = body["data"]["bosses"]
        assert len(bosses) >= 1
        for boss in bosses:
            assert boss["difficulty"] == "easy"

    def test_filter_by_hard_difficulty(self, test_app):
        resp = test_app.get("/api/v1/bosses?difficulty=hard")
        assert resp.status_code == 200
        body = resp.json()
        bosses = body["data"]["bosses"]
        assert len(bosses) >= 1
        for boss in bosses:
            assert boss["difficulty"] == "hard"

    def test_has_any_card_false_when_no_cards(self, test_app):
        from algomate.data.database import Database
        from algomate.models.cards import Card

        db = Database.get_instance()
        session = db.get_session()
        try:
            session.query(Card).delete()
            session.commit()
        finally:
            session.close()

        resp = test_app.get("/api/v1/bosses")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["has_any_card"] is False


class TestGetBossDetail:
    def test_returns_boss_detail_with_cards(self, test_app):
        resp = test_app.get("/api/v1/bosses/1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        data = body["data"]
        assert data["id"] == 1
        assert data["name"] == "测试Boss"
        assert data["difficulty"] == "easy"
        assert data["weakness_type"] == "basic_data_structure"
        assert "weakness_cards" in data
        assert "other_cards" in data
        assert "has_weakness_card" in data
        assert "recent_battles" in data
        assert isinstance(data["weakness_cards"], list)
        assert isinstance(data["other_cards"], list)
        assert isinstance(data["recent_battles"], list)

    def test_weakness_card_has_is_weakness_true(self, test_app):
        resp = test_app.get("/api/v1/bosses/1")
        body = resp.json()
        weakness_cards = body["data"]["weakness_cards"]
        assert len(weakness_cards) >= 1
        for card in weakness_cards:
            assert card["is_weakness"] is True
            assert card["algorithm_type"] == "basic_data_structure"

    def test_other_card_has_is_weakness_false(self, test_app):
        resp = test_app.get("/api/v1/bosses/1")
        body = resp.json()
        other_cards = body["data"]["other_cards"]
        assert len(other_cards) >= 1
        for card in other_cards:
            assert card["is_weakness"] is False

    def test_nonexistent_boss_returns_40403(self, test_app):
        resp = test_app.get("/api/v1/bosses/9999")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 40403
        assert body["message"] == "Boss不存在"


class TestChallengeBoss:
    def test_challenge_success_returns_battle_and_question(self, test_app):
        with patch(QG_PATCH, return_value=_mock_question_generator()):
            with patch(PICK_TYPE_PATCH, return_value="choice"):
                resp = test_app.post(
                    "/api/v1/bosses/1/challenge",
                    json={"card_id": 1},
                )
                assert resp.status_code == 200
                body = resp.json()
                assert body["code"] == 200
                data = body["data"]
                assert "battle_id" in data
                assert isinstance(data["battle_id"], int)
                assert data["question_type"] == "choice"
                assert "question" in data
                assert "is_weakness_card" in data

    def test_challenge_with_weakness_card_marks_true(self, test_app):
        with patch(QG_PATCH, return_value=_mock_question_generator()):
            with patch(PICK_TYPE_PATCH, return_value="choice"):
                resp = test_app.post(
                    "/api/v1/bosses/1/challenge",
                    json={"card_id": 1},
                )
                body = resp.json()
                assert body["data"]["is_weakness_card"] is True

    def test_challenge_with_normal_card_marks_false(self, test_app):
        with patch(QG_PATCH, return_value=_mock_question_generator()):
            with patch(PICK_TYPE_PATCH, return_value="choice"):
                resp = test_app.post(
                    "/api/v1/bosses/1/challenge",
                    json={"card_id": 2},
                )
                body = resp.json()
                assert body["data"]["is_weakness_card"] is False

    def test_challenge_missing_card_id_returns_40001(self, test_app):
        resp = test_app.post("/api/v1/bosses/1/challenge", json={})
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 40001

    def test_challenge_nonexistent_boss_returns_40403(self, test_app):
        resp = test_app.post(
            "/api/v1/bosses/9999/challenge",
            json={"card_id": 1},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 40403

    def test_challenge_nonexistent_card_returns_40404(self, test_app):
        resp = test_app.post(
            "/api/v1/bosses/1/challenge",
            json={"card_id": 9999},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 40404

    def test_challenge_no_cards_returns_40404(self, test_app):
        from algomate.data.database import Database
        from algomate.models.cards import Card

        db = Database.get_instance()
        session = db.get_session()
        try:
            session.query(Card).delete()
            session.commit()
        finally:
            session.close()

        resp = test_app.post(
            "/api/v1/bosses/1/challenge",
            json={"card_id": 9999},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 40404

    def test_challenge_short_answer_type(self, test_app):
        with patch(QG_PATCH, return_value=_mock_question_generator()):
            with patch(PICK_TYPE_PATCH, return_value="short_answer"):
                resp = test_app.post(
                    "/api/v1/bosses/1/challenge",
                    json={"card_id": 1},
                )
                body = resp.json()
                assert body["code"] == 200
                assert body["data"]["question_type"] == "short_answer"
                assert "content" in body["data"]["question"]

    def test_challenge_leetcode_type(self, test_app):
        with patch(QG_PATCH, return_value=_mock_question_generator()):
            with patch(PICK_TYPE_PATCH, return_value="leetcode"):
                resp = test_app.post(
                    "/api/v1/bosses/1/challenge",
                    json={"card_id": 1},
                )
                body = resp.json()
                assert body["code"] == 200
                assert body["data"]["question_type"] == "leetcode"
                assert "leetcode_url" in body["data"]["question"]
                assert "leetcode_title" in body["data"]["question"]


class TestSubmitBossAnswer:
    def _create_battle(self, test_app, card_id=1, question_type="choice"):
        with patch(QG_PATCH, return_value=_mock_question_generator()):
            with patch(PICK_TYPE_PATCH, return_value=question_type):
                resp = test_app.post(
                    "/api/v1/bosses/1/challenge",
                    json={"card_id": card_id},
                )
                return resp.json()["data"]["battle_id"]

    def test_choice_correct_answer_returns_victory_and_durability_plus_20(self, test_app):
        battle_id = self._create_battle(test_app, card_id=2, question_type="choice")

        from algomate.data.database import Database
        from algomate.models.battle_records import BattleRecord

        db = Database.get_instance()
        session = db.get_session()
        try:
            battle = session.query(BattleRecord).filter(BattleRecord.id == battle_id).first()
            correct_answer = battle.correct_answer
        finally:
            session.close()

        resp = test_app.post(
            "/api/v1/bosses/1/submit",
            json={
                "battle_id": battle_id,
                "answer": correct_answer,
                "question_type": "choice",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        data = body["data"]
        assert data["is_victory"] is True
        assert data["durability_change"] == 20
        assert data["is_weakness_card"] is False

    def test_choice_wrong_answer_returns_defeat_and_durability_minus_5(self, test_app):
        battle_id = self._create_battle(test_app, card_id=2, question_type="choice")

        resp = test_app.post(
            "/api/v1/bosses/1/submit",
            json={
                "battle_id": battle_id,
                "answer": "WRONG_ANSWER",
                "question_type": "choice",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        data = body["data"]
        assert data["is_victory"] is False
        assert data["durability_change"] == -5
        assert data["correct_answer"] != ""
        assert data["explanation"] != ""

    def test_weakness_card_victory_durability_plus_30(self, test_app):
        battle_id = self._create_battle(test_app, card_id=1, question_type="choice")

        from algomate.data.database import Database
        from algomate.models.battle_records import BattleRecord

        db = Database.get_instance()
        session = db.get_session()
        try:
            battle = session.query(BattleRecord).filter(BattleRecord.id == battle_id).first()
            correct_answer = battle.correct_answer
        finally:
            session.close()

        resp = test_app.post(
            "/api/v1/bosses/1/submit",
            json={
                "battle_id": battle_id,
                "answer": correct_answer,
                "question_type": "choice",
            },
        )
        body = resp.json()
        data = body["data"]
        assert data["is_victory"] is True
        assert data["durability_change"] == 30
        assert data["is_weakness_card"] is True

    def test_leetcode_solved_returns_victory(self, test_app):
        battle_id = self._create_battle(test_app, card_id=1, question_type="leetcode")

        resp = test_app.post(
            "/api/v1/bosses/1/submit",
            json={
                "battle_id": battle_id,
                "answer": "已完成",
                "question_type": "leetcode",
                "is_solved": True,
            },
        )
        body = resp.json()
        data = body["data"]
        assert data["is_victory"] is True

    def test_leetcode_not_solved_returns_defeat(self, test_app):
        battle_id = self._create_battle(test_app, card_id=1, question_type="leetcode")

        resp = test_app.post(
            "/api/v1/bosses/1/submit",
            json={
                "battle_id": battle_id,
                "answer": "未完成",
                "question_type": "leetcode",
                "is_solved": False,
            },
        )
        body = resp.json()
        data = body["data"]
        assert data["is_victory"] is False

    def test_missing_battle_id_returns_40001(self, test_app):
        resp = test_app.post(
            "/api/v1/bosses/1/submit",
            json={"answer": "A", "question_type": "choice"},
        )
        body = resp.json()
        assert body["code"] == 40001

    def test_unsupported_question_type_returns_40001(self, test_app):
        battle_id = self._create_battle(test_app, card_id=1, question_type="choice")

        resp = test_app.post(
            "/api/v1/bosses/1/submit",
            json={
                "battle_id": battle_id,
                "answer": "A",
                "question_type": "unsupported_type",
            },
        )
        body = resp.json()
        assert body["code"] == 40001

    def test_victory_guide_continue_challenge_true(self, test_app):
        battle_id = self._create_battle(test_app, card_id=2, question_type="choice")

        from algomate.data.database import Database
        from algomate.models.battle_records import BattleRecord

        db = Database.get_instance()
        session = db.get_session()
        try:
            battle = session.query(BattleRecord).filter(BattleRecord.id == battle_id).first()
            correct_answer = battle.correct_answer
        finally:
            session.close()

        resp = test_app.post(
            "/api/v1/bosses/1/submit",
            json={
                "battle_id": battle_id,
                "answer": correct_answer,
                "question_type": "choice",
            },
        )
        body = resp.json()
        guide = body["data"]["guide"]
        assert "available_actions" in guide
        assert "message" in guide

    def test_defeat_guide_go_review_true(self, test_app):
        battle_id = self._create_battle(test_app, card_id=2, question_type="choice")

        resp = test_app.post(
            "/api/v1/bosses/1/submit",
            json={
                "battle_id": battle_id,
                "answer": "WRONG_ANSWER",
                "question_type": "choice",
            },
        )
        body = resp.json()
        guide = body["data"]["guide"]
        assert "available_actions" in guide
        assert "message" in guide

    def test_short_answer_with_mock_evaluator(self, test_app):
        battle_id = self._create_battle(test_app, card_id=1, question_type="short_answer")

        with patch(AE_PATCH, return_value=_mock_answer_evaluator()):
            resp = test_app.post(
                "/api/v1/bosses/1/submit",
                json={
                    "battle_id": battle_id,
                    "answer": "动态规划的核心是分解子问题",
                    "question_type": "short_answer",
                },
            )
            body = resp.json()
            assert body["code"] == 200
            data = body["data"]
            assert "score" in data
            assert "feedback" in data

    def test_nonexistent_boss_returns_40403(self, test_app):
        resp = test_app.post(
            "/api/v1/bosses/9999/submit",
            json={"battle_id": 1, "answer": "A", "question_type": "choice"},
        )
        body = resp.json()
        assert body["code"] == 40403

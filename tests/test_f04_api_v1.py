import asyncio
import sys
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from algomate.api.routes import review_v1_router
from algomate.core.scheduler.review_scheduler import ReviewTask, TaskType


def _make_task(task_id="review_1", task_type="critical_review", card_id=1,
               card_name="test_card", card_algorithm_type="dp",
               card_durability=20, priority="critical", reason="濒危卡牌"):
    return ReviewTask(
        task_id=task_id,
        task_type=TaskType(task_type),
        card_id=card_id,
        card_name=card_name,
        card_algorithm_type=card_algorithm_type,
        card_durability=card_durability,
        priority=priority,
        reason=reason,
        due_date=date.today(),
        algorithm_type=card_algorithm_type,
        max_durability=100,
        review_level=0,
        next_review_date=None,
        review_types=["content_review"],
    )


def _mock_db(card_count=0, card_first=None):
    mock_db = MagicMock()
    mock_session = MagicMock()
    mock_db.get_session.return_value = mock_session
    mock_session.query.return_value.count.return_value = card_count
    mock_session.query.return_value.filter.return_value.first.return_value = card_first
    return mock_db, mock_session


def _run(coro):
    return asyncio.run(coro)


class TestReviewV1RouteRegistration:

    def test_router_has_correct_prefix(self):
        assert review_v1_router.prefix == "/v1/reviews"

    def test_router_has_today_endpoint(self):
        route_paths = [r.path for r in review_v1_router.routes]
        assert any("/today" in p for p in route_paths)

    def test_router_has_complete_endpoint(self):
        route_paths = [r.path for r in review_v1_router.routes]
        assert any("/{card_id}/complete" in p for p in route_paths)

    def test_router_has_quiz_endpoint(self):
        route_paths = [r.path for r in review_v1_router.routes]
        assert any("/{card_id}/quiz" in p for p in route_paths)

    def test_today_endpoint_is_get(self):
        for route in review_v1_router.routes:
            if "/today" in route.path:
                assert "GET" in route.methods
                break

    def test_complete_endpoint_is_post(self):
        for route in review_v1_router.routes:
            if "/{card_id}/complete" in route.path:
                assert "POST" in route.methods
                break

    def test_quiz_endpoint_is_post(self):
        for route in review_v1_router.routes:
            if "/{card_id}/quiz" in route.path:
                assert "POST" in route.methods
                break


class TestGetTodayReviewTasks:

    @patch("algomate.core.scheduler.review_scheduler.ReviewScheduler")
    @patch("algomate.data.database.Database")
    def test_returns_tasks_with_priority(self, MockDB, MockScheduler):
        from algomate.api.routes import get_today_review_tasks

        mock_db, mock_session = _mock_db(card_count=3)
        MockDB.get_instance.return_value = mock_db

        task1 = _make_task(priority="critical", card_durability=10)
        task2 = _make_task(task_id="review_2", task_type="forgetting_curve_review",
                           priority="high", card_durability=50, card_id=2)
        task3 = _make_task(task_id="review_3", task_type="boss_challenge",
                           priority="low", card_durability=80, card_id=3)

        mock_scheduler = MockScheduler.return_value
        mock_scheduler.generate_daily_tasks.return_value = [task1, task2, task3]

        result = _run(get_today_review_tasks())

        assert result["code"] == 200
        assert result["data"]["total_count"] == 3
        assert result["data"]["endangered_count"] == 1
        assert result["data"]["due_count"] == 1
        assert result["data"]["has_cards"] is True
        assert len(result["data"]["tasks"]) == 3
        for task in result["data"]["tasks"]:
            assert "review_types" in task
            assert task["review_types"] == ["content_review", "quick_quiz", "boss_challenge"]

    @patch("algomate.core.scheduler.review_scheduler.ReviewScheduler")
    @patch("algomate.data.database.Database")
    def test_has_cards_false_when_no_cards(self, MockDB, MockScheduler):
        from algomate.api.routes import get_today_review_tasks

        mock_db, mock_session = _mock_db(card_count=0)
        MockDB.get_instance.return_value = mock_db

        mock_scheduler = MockScheduler.return_value
        mock_scheduler.generate_daily_tasks.return_value = []

        result = _run(get_today_review_tasks())

        assert result["code"] == 200
        assert result["data"]["has_cards"] is False

    @patch("algomate.core.scheduler.review_scheduler.ReviewScheduler")
    @patch("algomate.data.database.Database")
    def test_empty_when_no_due(self, MockDB, MockScheduler):
        from algomate.api.routes import get_today_review_tasks

        mock_db, mock_session = _mock_db(card_count=5)
        MockDB.get_instance.return_value = mock_db

        mock_scheduler = MockScheduler.return_value
        mock_scheduler.generate_daily_tasks.return_value = []

        result = _run(get_today_review_tasks())

        assert result["code"] == 200
        assert result["data"]["tasks"] == []
        assert result["data"]["total_count"] == 0
        assert result["data"]["endangered_count"] == 0
        assert result["data"]["has_cards"] is True


class TestCompleteReviewV1:

    @patch("algomate.review.review_plan_service.ReviewPlanService")
    @patch("algomate.data.database.Database")
    def test_complete_review_with_valid_type(self, MockDB, MockService):
        from algomate.api.routes import complete_review_v1

        mock_card = MagicMock()
        mock_card.pending_retake = False
        mock_db, mock_session = _mock_db(card_first=mock_card)
        MockDB.get_instance.return_value = mock_db

        complete_result = {
            "card_id": 1,
            "card_name": "test",
            "review_type": "content_review",
            "durability_before": 50,
            "durability_after": 80,
        }
        mock_service = MockService.return_value
        mock_service.complete_review.return_value = complete_result

        result = _run(complete_review_v1(1, {"review_type": "content_review"}))

        assert result["code"] == 200
        assert result["data"]["review_type"] == "content_review"

    def test_complete_review_invalid_review_type(self):
        from algomate.api.routes import complete_review_v1

        with pytest.raises(HTTPException) as exc_info:
            _run(complete_review_v1(1, {"review_type": "invalid_type"}))
        assert exc_info.value.status_code == 400

    @patch("algomate.data.database.Database")
    def test_complete_review_card_not_found(self, MockDB):
        from algomate.api.routes import complete_review_v1

        mock_db, mock_session = _mock_db(card_first=None)
        MockDB.get_instance.return_value = mock_db

        with pytest.raises(HTTPException) as exc_info:
            _run(complete_review_v1(999, {"review_type": "content_review"}))
        assert exc_info.value.status_code == 404

    @patch("algomate.data.database.Database")
    def test_complete_review_sealed_card(self, MockDB):
        from algomate.api.routes import complete_review_v1

        mock_card = MagicMock()
        mock_card.pending_retake = True
        mock_db, mock_session = _mock_db(card_first=mock_card)
        MockDB.get_instance.return_value = mock_db

        with pytest.raises(HTTPException) as exc_info:
            _run(complete_review_v1(1, {"review_type": "content_review"}))
        assert exc_info.value.status_code == 409


class TestGenerateReviewQuizV1:

    @patch("algomate.core.agent.question_generator.QuestionGenerator")
    @patch("algomate.data.database.Database")
    def test_generate_quiz_success(self, MockDB, MockGenerator):
        from algomate.api.routes import generate_review_quiz_v1

        mock_card = MagicMock()
        mock_db, mock_session = _mock_db(card_first=mock_card)
        MockDB.get_instance.return_value = mock_db

        questions = [
            {"question_type": "选择题", "content": "test question", "answer": "A"},
        ]
        mock_generator = MockGenerator.return_value
        mock_generator.generate_review_quiz.return_value = questions

        result = _run(generate_review_quiz_v1(1, {"count": 2}))

        assert result["code"] == 200
        assert result["data"]["card_id"] == 1
        assert len(result["data"]["questions"]) == 1

    @patch("algomate.data.database.Database")
    def test_generate_quiz_card_not_found(self, MockDB):
        from algomate.api.routes import generate_review_quiz_v1

        mock_db, mock_session = _mock_db(card_first=None)
        MockDB.get_instance.return_value = mock_db

        with pytest.raises(HTTPException) as exc_info:
            _run(generate_review_quiz_v1(999, {"count": 2}))
        assert exc_info.value.status_code == 404

    @patch("algomate.core.agent.question_generator.QuestionGenerator")
    @patch("algomate.data.database.Database")
    def test_generate_quiz_timeout_returns_504(self, MockDB, MockGenerator):
        from algomate.api.routes import generate_review_quiz_v1

        mock_card = MagicMock()
        mock_db, mock_session = _mock_db(card_first=mock_card)
        MockDB.get_instance.return_value = mock_db

        mock_generator = MockGenerator.return_value
        mock_generator.generate_review_quiz.side_effect = TimeoutError("AI timeout")

        with pytest.raises(HTTPException) as exc_info:
            _run(generate_review_quiz_v1(1, {"count": 2}))
        assert exc_info.value.status_code == 504

    @patch("algomate.core.agent.question_generator.QuestionGenerator")
    @patch("algomate.data.database.Database")
    def test_generate_quiz_rate_limit_returns_429(self, MockDB, MockGenerator):
        from algomate.api.routes import generate_review_quiz_v1

        mock_card = MagicMock()
        mock_db, mock_session = _mock_db(card_first=mock_card)
        MockDB.get_instance.return_value = mock_db

        mock_generator = MockGenerator.return_value
        mock_generator.generate_review_quiz.side_effect = Exception("rate limit exceeded 429")

        with pytest.raises(HTTPException) as exc_info:
            _run(generate_review_quiz_v1(1, {"count": 2}))
        assert exc_info.value.status_code == 429

    @patch("algomate.core.agent.question_generator.QuestionGenerator")
    @patch("algomate.data.database.Database")
    def test_generate_quiz_generic_error_returns_500(self, MockDB, MockGenerator):
        from algomate.api.routes import generate_review_quiz_v1

        mock_card = MagicMock()
        mock_db, mock_session = _mock_db(card_first=mock_card)
        MockDB.get_instance.return_value = mock_db

        mock_generator = MockGenerator.return_value
        mock_generator.generate_review_quiz.side_effect = Exception("unknown error")

        with pytest.raises(HTTPException) as exc_info:
            _run(generate_review_quiz_v1(1, {"count": 2}))
        assert exc_info.value.status_code == 500

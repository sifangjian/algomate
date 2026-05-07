import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta

from algomate.core.scheduler.review_scheduler import ReviewTask, TaskType, PRIORITY_ORDER
from algomate.core.memory.forgotten_curve import ReviewAction
from algomate.models.cards import Card


@pytest.fixture(autouse=True)
def _add_is_sealed_to_card():
    if not hasattr(Card, 'is_sealed'):
        Card.is_sealed = MagicMock()
        yield
        delattr(Card, 'is_sealed')
    else:
        yield


class TestCompleteReview:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.mock_session = MagicMock()
        self.mock_db.get_session.return_value = self.mock_session

    @patch("algomate.review.review_plan_service.ReviewRecord")
    @patch("algomate.review.review_plan_service.ForgottenCurveEngine")
    @patch("algomate.review.review_plan_service.ReviewRecordRepository")
    def test_complete_review_accepts_review_type(self, MockRepo, MockCurve, MockRecord):
        from algomate.review.review_plan_service import ReviewPlanService

        mock_card = MagicMock()
        mock_card.id = 1
        mock_card.name = "二分查找"
        mock_card.durability = 60
        mock_card.review_level = 2
        mock_card.review_count = 5
        mock_card.next_review_date = datetime(2025, 6, 1, 10, 0)

        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_card
        self.mock_session.query.return_value.filter.return_value.all.return_value = []
        self.mock_session.query.return_value.filter.return_value.count.return_value = 3

        service = ReviewPlanService(db=self.mock_db)
        result = service.complete_review(card_id=1, review_type="content_review")

        assert result is not None
        assert result["review_type"] == "content_review"

    @patch("algomate.review.review_plan_service.ReviewRecord")
    @patch("algomate.review.review_plan_service.ForgottenCurveEngine")
    @patch("algomate.review.review_plan_service.ReviewRecordRepository")
    def test_complete_review_records_durability_and_review_level(self, MockRepo, MockCurve, MockRecord):
        from algomate.review.review_plan_service import ReviewPlanService

        mock_card = MagicMock()
        mock_card.id = 1
        mock_card.name = "快速排序"
        mock_card.durability = 50
        mock_card.review_level = 2
        mock_card.review_count = 3
        mock_card.next_review_date = datetime(2025, 6, 1, 10, 0)

        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_card
        self.mock_session.query.return_value.filter.return_value.all.return_value = []
        self.mock_session.query.return_value.filter.return_value.count.return_value = 2

        mock_curve = MockCurve.return_value

        def side_effect(card, action):
            card.durability = 70
            card.review_level = 3
            card.next_review_date = datetime(2025, 6, 15, 10, 0)
            card.last_reviewed = datetime.now()
            card.review_count = 4
            return 3, date(2025, 6, 15)

        mock_curve.complete_review_for_card.side_effect = side_effect

        service = ReviewPlanService(db=self.mock_db)
        result = service.complete_review(card_id=1, review_type="quiz_review")

        assert result["durability_before"] == 50
        assert result["durability_after"] == 70
        assert result["review_level_before"] == 2
        assert result["review_level_after"] == 3

    @patch("algomate.review.review_plan_service.ReviewRecord")
    @patch("algomate.review.review_plan_service.ForgottenCurveEngine")
    @patch("algomate.review.review_plan_service.ReviewRecordRepository")
    def test_complete_review_calculates_remaining_endangered(self, MockRepo, MockCurve, MockRecord):
        from algomate.review.review_plan_service import ReviewPlanService

        mock_card = MagicMock()
        mock_card.id = 1
        mock_card.name = "归并排序"
        mock_card.durability = 40
        mock_card.review_level = 1
        mock_card.review_count = 2
        mock_card.next_review_date = datetime(2025, 6, 1, 10, 0)

        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_card
        self.mock_session.query.return_value.filter.return_value.all.return_value = []
        self.mock_session.query.return_value.filter.return_value.count.return_value = 7

        service = ReviewPlanService(db=self.mock_db)
        result = service.complete_review(card_id=1)

        assert result["remaining_endangered"] == 7

    @patch("algomate.review.review_plan_service.ReviewRecord")
    @patch("algomate.review.review_plan_service.ForgottenCurveEngine")
    @patch("algomate.review.review_plan_service.ReviewRecordRepository")
    def test_complete_review_returns_none_for_missing_card(self, MockRepo, MockCurve, MockRecord):
        from algomate.review.review_plan_service import ReviewPlanService

        self.mock_session.query.return_value.filter.return_value.first.return_value = None

        service = ReviewPlanService(db=self.mock_db)
        result = service.complete_review(card_id=999)

        assert result is None

    @patch("algomate.review.review_plan_service.ReviewRecord")
    @patch("algomate.review.review_plan_service.ForgottenCurveEngine")
    @patch("algomate.review.review_plan_service.ReviewRecordRepository")
    def test_complete_review_always_uses_success_action(self, MockRepo, MockCurve, MockRecord):
        from algomate.review.review_plan_service import ReviewPlanService

        mock_card = MagicMock()
        mock_card.id = 1
        mock_card.name = "堆排序"
        mock_card.durability = 55
        mock_card.review_level = 1
        mock_card.review_count = 1
        mock_card.next_review_date = datetime(2025, 6, 1, 10, 0)

        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_card
        self.mock_session.query.return_value.filter.return_value.all.return_value = []
        self.mock_session.query.return_value.filter.return_value.count.return_value = 0

        mock_curve = MockCurve.return_value
        mock_curve.complete_review_for_card.return_value = (2, date(2025, 6, 4))

        service = ReviewPlanService(db=self.mock_db)
        service.complete_review(card_id=1, review_type="content_review")

        mock_curve.complete_review_for_card.assert_called_once_with(
            mock_card, ReviewAction.SUCCESS
        )

    @patch("algomate.review.review_plan_service.ReviewRecord")
    @patch("algomate.review.review_plan_service.ForgottenCurveEngine")
    @patch("algomate.review.review_plan_service.ReviewRecordRepository")
    def test_complete_review_creates_review_record_with_new_fields(self, MockRepo, MockCurve, MockRecord):
        from algomate.review.review_plan_service import ReviewPlanService

        mock_card = MagicMock()
        mock_card.id = 1
        mock_card.name = "插入排序"
        mock_card.durability = 45
        mock_card.review_level = 1
        mock_card.review_count = 2
        mock_card.next_review_date = datetime(2025, 6, 1, 10, 0)

        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_card
        self.mock_session.query.return_value.filter.return_value.all.return_value = []
        self.mock_session.query.return_value.filter.return_value.count.return_value = 0

        mock_curve = MockCurve.return_value

        def side_effect(card, action):
            card.durability = 65
            card.review_level = 2
            card.next_review_date = datetime(2025, 6, 4, 10, 0)
            card.last_reviewed = datetime.now()
            card.review_count = 3
            return 2, date(2025, 6, 4)

        mock_curve.complete_review_for_card.side_effect = side_effect

        service = ReviewPlanService(db=self.mock_db)
        service.complete_review(card_id=1, review_type="quiz_review")

        MockRecord.assert_called_once()
        call_kwargs = MockRecord.call_args.kwargs
        assert call_kwargs["review_type"] == "quiz_review"
        assert call_kwargs["completed_at"] is not None
        assert call_kwargs["durability_before"] == 45
        assert call_kwargs["durability_after"] == 65
        assert call_kwargs["review_level_before"] == 1
        assert call_kwargs["review_level_after"] == 2

    @patch("algomate.review.review_plan_service.ReviewRecord")
    @patch("algomate.review.review_plan_service.ForgottenCurveEngine")
    @patch("algomate.review.review_plan_service.ReviewRecordRepository")
    def test_complete_review_default_review_type(self, MockRepo, MockCurve, MockRecord):
        from algomate.review.review_plan_service import ReviewPlanService

        mock_card = MagicMock()
        mock_card.id = 1
        mock_card.name = "冒泡排序"
        mock_card.durability = 30
        mock_card.review_level = 0
        mock_card.review_count = 0
        mock_card.next_review_date = datetime(2025, 6, 1, 10, 0)

        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_card
        self.mock_session.query.return_value.filter.return_value.all.return_value = []
        self.mock_session.query.return_value.filter.return_value.count.return_value = 0

        service = ReviewPlanService(db=self.mock_db)
        result = service.complete_review(card_id=1)

        assert result["review_type"] == "content_review"


class TestReviewSchedulerSorting:
    def test_priority_order_mapping(self):
        assert PRIORITY_ORDER["critical"] == 0
        assert PRIORITY_ORDER["high"] == 1
        assert PRIORITY_ORDER["medium"] == 2
        assert PRIORITY_ORDER["low"] == 3

    def test_tasks_sorted_by_priority(self):
        tasks = [
            ReviewTask(
                task_id="1", task_type=TaskType.BOSS_CHALLENGE,
                card_id=1, card_name="A", card_algorithm_type="sort",
                card_durability=50, priority="low", reason="Boss挑战",
            ),
            ReviewTask(
                task_id="2", task_type=TaskType.FORGETTING_CURVE_REVIEW,
                card_id=2, card_name="B", card_algorithm_type="dp",
                card_durability=60, priority="medium", reason="遗忘曲线",
            ),
            ReviewTask(
                task_id="3", task_type=TaskType.CRITICAL_REVIEW,
                card_id=3, card_name="C", card_algorithm_type="graph",
                card_durability=10, priority="critical", reason="濒危",
            ),
            ReviewTask(
                task_id="4", task_type=TaskType.FORGETTING_CURVE_REVIEW,
                card_id=4, card_name="D", card_algorithm_type="tree",
                card_durability=70, priority="high", reason="遗忘曲线",
            ),
        ]

        tasks.sort(key=lambda t: (PRIORITY_ORDER.get(t.priority, 3), t.card_durability))

        assert tasks[0].priority == "critical"
        assert tasks[1].priority == "high"
        assert tasks[2].priority == "medium"
        assert tasks[3].priority == "low"

    def test_same_priority_lower_durability_first(self):
        tasks = [
            ReviewTask(
                task_id="1", task_type=TaskType.CRITICAL_REVIEW,
                card_id=1, card_name="A", card_algorithm_type="sort",
                card_durability=25, priority="critical", reason="濒危",
            ),
            ReviewTask(
                task_id="2", task_type=TaskType.CRITICAL_REVIEW,
                card_id=2, card_name="B", card_algorithm_type="dp",
                card_durability=10, priority="critical", reason="濒危",
            ),
            ReviewTask(
                task_id="3", task_type=TaskType.CRITICAL_REVIEW,
                card_id=3, card_name="C", card_algorithm_type="graph",
                card_durability=15, priority="critical", reason="濒危",
            ),
        ]

        tasks.sort(key=lambda t: (PRIORITY_ORDER.get(t.priority, 3), t.card_durability))

        assert tasks[0].card_durability == 10
        assert tasks[1].card_durability == 15
        assert tasks[2].card_durability == 25

    def test_all_four_priority_levels(self):
        tasks = [
            ReviewTask(
                task_id="1", task_type=TaskType.FORGETTING_CURVE_REVIEW,
                card_id=1, card_name="A", card_algorithm_type="sort",
                card_durability=50, priority="medium", reason="遗忘曲线",
            ),
            ReviewTask(
                task_id="2", task_type=TaskType.CRITICAL_REVIEW,
                card_id=2, card_name="B", card_algorithm_type="dp",
                card_durability=10, priority="critical", reason="濒危",
            ),
            ReviewTask(
                task_id="3", task_type=TaskType.BOSS_CHALLENGE,
                card_id=3, card_name="C", card_algorithm_type="graph",
                card_durability=80, priority="low", reason="Boss挑战",
            ),
            ReviewTask(
                task_id="4", task_type=TaskType.FORGETTING_CURVE_REVIEW,
                card_id=4, card_name="D", card_algorithm_type="tree",
                card_durability=60, priority="high", reason="遗忘曲线",
            ),
        ]

        tasks.sort(key=lambda t: (PRIORITY_ORDER.get(t.priority, 3), t.card_durability))

        priorities = [t.priority for t in tasks]
        assert priorities == ["critical", "high", "medium", "low"]

    def test_unknown_priority_defaults_to_lowest(self):
        result = PRIORITY_ORDER.get("unknown", 3)
        assert result == 3


class TestReviewTaskNewFields:
    def test_review_task_new_fields_defaults(self):
        task = ReviewTask(
            task_id="review_1",
            task_type=TaskType.CRITICAL_REVIEW,
            card_id=1,
            card_name="二分查找",
            card_algorithm_type="搜索",
            card_durability=10,
            priority="critical",
            reason="濒危卡牌",
        )
        assert task.algorithm_type == ""
        assert task.max_durability == 100
        assert task.review_level == 0
        assert task.next_review_date is None
        assert task.review_types is None

    def test_review_task_to_dict_includes_new_fields(self):
        task = ReviewTask(
            task_id="review_1",
            task_type=TaskType.CRITICAL_REVIEW,
            card_id=1,
            card_name="二分查找",
            card_algorithm_type="搜索",
            card_durability=10,
            priority="critical",
            reason="濒危卡牌",
            due_date=date(2025, 5, 6),
            algorithm_type="二分查找",
            max_durability=100,
            review_level=3,
            next_review_date=date(2025, 5, 10),
            review_types=["content_review"],
        )
        d = task.to_dict()
        assert d["algorithm_type"] == "二分查找"
        assert d["max_durability"] == 100
        assert d["review_level"] == 3
        assert d["next_review_date"] == "2025-05-10"
        assert d["review_types"] == ["content_review"]

    def test_review_task_to_dict_none_review_types(self):
        task = ReviewTask(
            task_id="review_1",
            task_type=TaskType.CRITICAL_REVIEW,
            card_id=1,
            card_name="二分查找",
            card_algorithm_type="搜索",
            card_durability=10,
            priority="critical",
            reason="濒危卡牌",
        )
        d = task.to_dict()
        assert d["review_types"] == []

    def test_review_task_to_dict_none_next_review_date(self):
        task = ReviewTask(
            task_id="review_1",
            task_type=TaskType.CRITICAL_REVIEW,
            card_id=1,
            card_name="二分查找",
            card_algorithm_type="搜索",
            card_durability=10,
            priority="critical",
            reason="濒危卡牌",
        )
        d = task.to_dict()
        assert d["next_review_date"] is None


class TestGenerateReviewQuiz:
    def setup_method(self):
        self.mock_chat_client = MagicMock()

    @patch("algomate.data.database.Database")
    def test_generate_review_quiz_returns_questions_for_valid_card(self, MockDB):
        from algomate.core.agent.question_generator import QuestionGenerator

        mock_session = MagicMock()
        MockDB.get_instance.return_value.get_session.return_value = mock_session

        mock_card = MagicMock()
        mock_card.id = 1
        mock_card.name = "快速排序"
        mock_card.knowledge_content = "快速排序是一种分治算法"
        mock_card.summary = None
        mock_card.algorithm_type = "排序算法"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_card

        generator = QuestionGenerator(chat_client=self.mock_chat_client)
        generator.generate_multiple_choice = MagicMock(return_value=[
            {"question_type": "选择题", "content": "快速排序的平均时间复杂度？", "answer": "O(n log n)"},
        ])

        result = generator.generate_review_quiz(card_id=1, count=2)

        assert len(result) == 1
        assert result[0]["card_id"] == 1
        assert result[0]["card_name"] == "快速排序"

    @patch("algomate.data.database.Database")
    def test_generate_review_quiz_returns_empty_for_invalid_card(self, MockDB):
        from algomate.core.agent.question_generator import QuestionGenerator

        mock_session = MagicMock()
        MockDB.get_instance.return_value.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        generator = QuestionGenerator(chat_client=self.mock_chat_client)
        result = generator.generate_review_quiz(card_id=999)

        assert result == []

    @patch("algomate.data.database.Database")
    def test_generate_review_quiz_count_clamped_to_range(self, MockDB):
        from algomate.core.agent.question_generator import QuestionGenerator

        mock_session = MagicMock()
        MockDB.get_instance.return_value.get_session.return_value = mock_session

        mock_card = MagicMock()
        mock_card.id = 1
        mock_card.name = "归并排序"
        mock_card.knowledge_content = "归并排序是稳定排序"
        mock_card.summary = None
        mock_card.algorithm_type = "排序算法"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_card

        generator = QuestionGenerator(chat_client=self.mock_chat_client)
        generator.generate_multiple_choice = MagicMock(return_value=[
            {"question_type": "选择题", "content": "Q1", "answer": "A"},
        ])

        generator.generate_review_quiz(card_id=1, count=0)
        call_args = generator.generate_multiple_choice.call_args
        assert call_args.kwargs["count"] == 1

        generator.generate_review_quiz(card_id=1, count=5)
        call_args = generator.generate_multiple_choice.call_args
        assert call_args.kwargs["count"] == 2

    @patch("algomate.data.database.Database")
    def test_generate_review_quiz_uses_knowledge_content(self, MockDB):
        from algomate.core.agent.question_generator import QuestionGenerator

        mock_session = MagicMock()
        MockDB.get_instance.return_value.get_session.return_value = mock_session

        mock_card = MagicMock()
        mock_card.id = 2
        mock_card.name = "堆排序"
        mock_card.knowledge_content = "堆排序利用堆数据结构"
        mock_card.summary = "堆排序摘要"
        mock_card.algorithm_type = "排序算法"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_card

        generator = QuestionGenerator(chat_client=self.mock_chat_client)
        generator.generate_multiple_choice = MagicMock(return_value=[])

        generator.generate_review_quiz(card_id=2, count=1)

        call_args = generator.generate_multiple_choice.call_args
        assert call_args.kwargs["note_content"] == "堆排序利用堆数据结构"

    @patch("algomate.data.database.Database")
    def test_generate_review_quiz_falls_back_to_summary(self, MockDB):
        from algomate.core.agent.question_generator import QuestionGenerator

        mock_session = MagicMock()
        MockDB.get_instance.return_value.get_session.return_value = mock_session

        mock_card = MagicMock()
        mock_card.id = 3
        mock_card.name = "DFS"
        mock_card.knowledge_content = None
        mock_card.summary = "深度优先搜索摘要"
        mock_card.algorithm_type = "搜索"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_card

        generator = QuestionGenerator(chat_client=self.mock_chat_client)
        generator.generate_multiple_choice = MagicMock(return_value=[])

        generator.generate_review_quiz(card_id=3, count=1)

        call_args = generator.generate_multiple_choice.call_args
        assert call_args.kwargs["note_content"] == "深度优先搜索摘要"

    @patch("algomate.data.database.Database")
    def test_generate_review_quiz_falls_back_to_name_and_type(self, MockDB):
        from algomate.core.agent.question_generator import QuestionGenerator

        mock_session = MagicMock()
        MockDB.get_instance.return_value.get_session.return_value = mock_session

        mock_card = MagicMock()
        mock_card.id = 4
        mock_card.name = "BFS"
        mock_card.knowledge_content = None
        mock_card.summary = None
        mock_card.algorithm_type = "搜索"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_card

        generator = QuestionGenerator(chat_client=self.mock_chat_client)
        generator.generate_multiple_choice = MagicMock(return_value=[])

        generator.generate_review_quiz(card_id=4, count=1)

        call_args = generator.generate_multiple_choice.call_args
        assert call_args.kwargs["note_content"] == "BFS 搜索"

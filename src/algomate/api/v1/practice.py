import logging

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/practice", tags=["练习"])
logger = logging.getLogger(__name__)


@router.get("/questions")
async def get_questions(question_type: str = None, count: int = 1, algorithm_type: str = None):
    from algomate.core.agent.question_generator import QuestionGenerator

    generator = QuestionGenerator()

    try:
        note_content = algorithm_type or "算法"
        if question_type == "选择题":
            questions = generator.generate_multiple_choice(
                note_content=note_content,
                count=count,
            )
        elif question_type == "简答题":
            questions = generator.generate_short_answer(
                note_content=note_content,
                count=count,
            )
        elif question_type == "LeetCode挑战":
            questions = []
            for _ in range(count):
                q = generator.generate_leetcode_challenge(
                    note_content=note_content,
                    algorithm_type=algorithm_type or "",
                )
                questions.append(q)
        else:
            questions = generator.generate_for_note(
                note_content=note_content,
                count=count,
            )
        return {"questions": questions}
    except Exception as e:
        logger.error("generate_questions failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
async def submit_answer(request: dict):
    from algomate.core.agent.answer_evaluator import AnswerEvaluator
    from algomate.data.database import Database

    question_id = request.get("question_id")
    user_answer = request.get("user_answer", "")
    question_type = request.get("question_type")

    if not question_id or not user_answer:
        raise HTTPException(status_code=400, detail="question_id 和 user_answer 不能为空")

    db = Database.get_instance()
    evaluator = AnswerEvaluator(db=db)

    try:
        result = evaluator.evaluate_by_question_id(question_id, user_answer)
        return {
            "is_correct": result.get("is_correct", False),
            "feedback": result.get("feedback", ""),
            "improvement": result.get("improvement", ""),
            "score": result.get("score", 0),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("submit_answer failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weak-points")
async def get_weak_points(days: int = 30, threshold: float = 0.7):
    from algomate.core.agent.weak_point_analyzer import WeakPointAnalyzer
    from algomate.data.database import Database

    db = Database.get_instance()
    analyzer = WeakPointAnalyzer(db=db)

    try:
        result = analyzer.analyze(days=days)
        weak_points = [
            wp for wp in result.get("weak_points", [])
            if wp.get("accuracy", 1.0) < threshold
        ]
        return {
            "weak_points": weak_points,
            "overall_accuracy": result.get("overall_accuracy", 0.0),
            "recommendations": result.get("recommendations", []),
        }
    except Exception as e:
        logger.error("get_weak_points failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

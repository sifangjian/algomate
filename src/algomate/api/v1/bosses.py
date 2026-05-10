import json
import logging
import random
import re

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/bosses", tags=["Boss挑战"])
logger = logging.getLogger(__name__)

_FALLBACK_CHOICE_QUESTIONS = [
    {
        "content": "以下哪个是二分查找的时间复杂度？",
        "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
        "correct_answer": "B",
        "explanation": "二分查找每次将搜索范围减半，因此时间复杂度为O(log n)",
    },
    {
        "content": "哈希表的平均查找时间复杂度是？",
        "options": ["O(n)", "O(log n)", "O(1)", "O(n^2)"],
        "correct_answer": "C",
        "explanation": "哈希表通过哈希函数直接定位元素，平均查找时间复杂度为O(1)",
    },
    {
        "content": "以下哪种数据结构适合实现函数调用栈？",
        "options": ["队列", "栈", "链表", "哈希表"],
        "correct_answer": "B",
        "explanation": "栈的后进先出特性完美匹配函数调用的嵌套关系",
    },
]

_FALLBACK_SHORT_ANSWER_QUESTIONS = [
    {
        "content": "请简述动态规划的核心思想",
        "correct_answer": "将复杂问题分解为重叠子问题，通过存储子问题的解避免重复计算，从底向上构建最优解",
        "explanation": "动态规划通过记忆化或制表法，将指数级问题降为多项式级",
    },
    {
        "content": "请简述深度优先搜索(DFS)的基本原理",
        "correct_answer": "从起始节点出发，沿一条路径尽可能深地探索，直到无法继续后回溯，再探索其他路径",
        "explanation": "DFS使用栈（或递归）实现，适合寻找所有解或判断连通性",
    },
]


def _has_available_bosses(db) -> bool:
    from algomate.models.bosses import Boss
    session = db.get_session()
    try:
        return session.query(Boss).count() > 0
    finally:
        session.close()


def _pick_question_type():
    r = random.random()
    if r < 0.4:
        return "choice"
    elif r < 0.8:
        return "short_answer"
    else:
        return "leetcode"


def _extract_options_from_content(content: str):
    options = {}
    option_pattern = r'([A-D])[.、：:]\s*([^\n]+)'
    matches = re.findall(option_pattern, content)
    for letter, text in matches:
        options[letter] = text.strip()
    return [options[k] for k in sorted(options.keys())] if options else []


def _get_fallback_choice():
    q = random.choice(_FALLBACK_CHOICE_QUESTIONS)
    return {
        "content": q["content"],
        "options": q["options"],
        "correct_answer": q["correct_answer"],
        "explanation": q["explanation"],
    }


def _get_fallback_short_answer():
    q = random.choice(_FALLBACK_SHORT_ANSWER_QUESTIONS)
    return {
        "content": q["content"],
        "correct_answer": q["correct_answer"],
        "explanation": q["explanation"],
    }


@router.get("")
async def get_bosses(difficulty: str = None):
    from algomate.data.database import Database
    from algomate.data.repositories.boss_repo import BossRepository
    from algomate.data.repositories.card_repo import CardRepository
    from algomate.models.cards import Card
    from sqlalchemy import func

    db = Database.get_instance()
    boss_repo = BossRepository(db)
    card_repo = CardRepository(db)

    try:
        bosses = boss_repo.get_all()
        if difficulty:
            bosses = [b for b in bosses if b.difficulty == difficulty]

        session = db.get_session()
        try:
            has_any_card = session.query(func.count(Card.id)).scalar() > 0
        finally:
            session.close()

        boss_list = []
        for boss in bosses:
            weakness_cards = card_repo.get_by_algorithm_type(boss.weakness_type)
            has_weakness_card = len(weakness_cards) > 0
            weakness_card_count = len(weakness_cards)
            boss_list.append({
                "id": boss.id,
                "name": boss.name,
                "difficulty": boss.difficulty,
                "weakness_type": boss.weakness_type,
                "description": boss.description,
                "has_weakness_card": has_weakness_card,
                "weakness_card_count": weakness_card_count,
            })

        return {
            "code": 200,
            "message": "success",
            "data": {
                "bosses": boss_list,
                "has_any_card": has_any_card,
            }
        }
    except Exception as e:
        logger.error("get_bosses failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{boss_id}")
async def get_boss_detail(boss_id: int):
    from algomate.data.database import Database
    from algomate.data.repositories.boss_repo import BossRepository
    from algomate.data.repositories.card_repo import CardRepository
    from algomate.data.repositories.battle_record_repo import BattleRecordRepository

    db = Database.get_instance()
    boss_repo = BossRepository(db)
    card_repo = CardRepository(db)
    battle_repo = BattleRecordRepository(db)

    boss = boss_repo.get_by_id(boss_id)
    if not boss:
        return {"code": 40403, "message": "Boss不存在"}

    all_cards = card_repo.get_all()
    weakness_cards = []
    other_cards = []
    for card in all_cards:
        if card.pending_retake:
            continue
        is_weakness = card.algorithm_type == boss.weakness_type
        card_info = {
            "id": card.id,
            "name": card.name,
            "algorithm_type": card.algorithm_type,
            "durability": card.durability,
            "is_weakness": is_weakness,
        }
        if is_weakness:
            weakness_cards.append(card_info)
        else:
            other_cards.append(card_info)

    has_any_card = len(weakness_cards) > 0 or len(other_cards) > 0

    recent_battles = battle_repo.get_recent_by_boss(boss_id, limit=5)
    recent_list = []
    for br in recent_battles:
        card_name = br.card.name if br.card else ""
        recent_list.append({
            "id": br.id,
            "card_name": card_name,
            "is_victory": br.is_victory,
            "question_type": br.question_type,
            "created_at": br.created_at.isoformat() if br.created_at else None,
        })

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": boss.id,
            "name": boss.name,
            "difficulty": boss.difficulty,
            "weakness_type": boss.weakness_type,
            "description": boss.description,
            "npc_id": boss.npc_id,
            "weakness_cards": weakness_cards,
            "other_cards": other_cards,
            "has_weakness_card": len(weakness_cards) > 0,
            "has_any_card": has_any_card,
            "recent_battles": recent_list,
        }
    }


@router.post("/{boss_id}/challenge")
async def challenge_boss(boss_id: int, request: dict):
    from algomate.data.database import Database
    from algomate.data.repositories.boss_repo import BossRepository
    from algomate.data.repositories.card_repo import CardRepository
    from algomate.data.repositories.battle_record_repo import BattleRecordRepository
    from algomate.core.agent.question_generator import QuestionGenerator

    card_id = request.get("card_id")
    if not card_id:
        return {"code": 40001, "message": "参数校验失败：card_id不能为空"}

    db = Database.get_instance()
    boss_repo = BossRepository(db)
    card_repo = CardRepository(db)
    battle_repo = BattleRecordRepository(db)

    boss = boss_repo.get_by_id(boss_id)
    if not boss:
        return {"code": 40403, "message": "Boss不存在"}

    card = card_repo.get_by_id(int(card_id))
    if not card:
        return {"code": 40404, "message": "卡牌不存在"}

    is_weakness_card = card.algorithm_type == boss.weakness_type

    session = db.get_session()
    try:
        from algomate.models.cards import Card
        total_cards = session.query(Card).count()
    finally:
        session.close()

    if total_cards == 0:
        return {"code": 40301, "message": "无卡牌无法挑战Boss"}

    question_type = _pick_question_type()
    question_data = {}

    try:
        generator = QuestionGenerator()
        note_content = card.core_concept or card.name or boss.weakness_type

        if question_type == "choice":
            questions = generator.generate_multiple_choice(
                note_content=note_content,
                count=1,
            )
            if questions:
                q = questions[0]
                options = q.get("options", [])
                if not options:
                    options = _extract_options_from_content(q.get("content", ""))
                question_data = {
                    "content": q.get("content", ""),
                    "options": options,
                    "correct_answer": q.get("answer", ""),
                    "explanation": q.get("explanation", ""),
                }
            else:
                question_data = _get_fallback_choice()
        elif question_type == "short_answer":
            questions = generator.generate_short_answer(
                note_content=note_content,
                count=1,
            )
            if questions:
                q = questions[0]
                question_data = {
                    "content": q.get("content", ""),
                    "correct_answer": q.get("answer", ""),
                    "explanation": q.get("explanation", ""),
                }
            else:
                question_data = _get_fallback_short_answer()
        else:
            q = generator.generate_leetcode_challenge(
                note_content=note_content,
                algorithm_type=boss.weakness_type,
            )
            question_data = {
                "content": q.get("content", ""),
                "leetcode_url": q.get("leetcode_url", ""),
                "leetcode_title": q.get("leetcode_title", ""),
                "leetcode_difficulty": q.get("leetcode_difficulty", ""),
                "explanation": q.get("explanation", ""),
            }
    except Exception:
        if question_type == "choice":
            question_data = _get_fallback_choice()
        elif question_type == "short_answer":
            question_data = _get_fallback_short_answer()
        else:
            question_data = {
                "content": "请在LeetCode上完成一道相关题目",
                "leetcode_url": "https://leetcode.cn/problemset/all/",
                "leetcode_title": "LeetCode练习",
                "leetcode_difficulty": "medium",
                "explanation": "",
            }

    record = battle_repo.create(
        boss_id=boss_id,
        card_id=int(card_id),
        question_type=question_type,
        is_weakness_card=is_weakness_card,
        question_content=question_data.get("content", ""),
        question_options=json.dumps(question_data.get("options"), ensure_ascii=False) if question_data.get("options") else None,
        correct_answer=question_data.get("correct_answer", ""),
        explanation=question_data.get("explanation", ""),
        leetcode_url=question_data.get("leetcode_url"),
    )

    response_question = {}
    if question_type == "choice":
        response_question = {
            "content": question_data.get("content", ""),
            "options": question_data.get("options", []),
        }
    elif question_type == "short_answer":
        response_question = {
            "content": question_data.get("content", ""),
        }
    else:
        response_question = {
            "content": question_data.get("content", ""),
            "leetcode_url": question_data.get("leetcode_url", ""),
            "leetcode_title": question_data.get("leetcode_title", ""),
            "leetcode_difficulty": question_data.get("leetcode_difficulty", ""),
        }

    return {
        "code": 200,
        "message": "success",
        "data": {
            "battle_id": record.id,
            "question_type": question_type,
            "is_weakness_card": is_weakness_card,
            "question": response_question,
        }
    }


@router.post("/{boss_id}/submit")
async def submit_boss_answer(boss_id: int, request: dict):
    from algomate.data.database import Database
    from algomate.data.repositories.boss_repo import BossRepository
    from algomate.data.repositories.card_repo import CardRepository
    from algomate.data.repositories.battle_record_repo import BattleRecordRepository
    from algomate.core.agent.answer_evaluator import AnswerEvaluator
    from algomate.core.guide.service import GuideService

    battle_id = request.get("battle_id")
    answer = request.get("answer", "")
    question_type = request.get("question_type")
    is_solved = request.get("is_solved", False)

    if not battle_id:
        return {"code": 40001, "message": "参数校验失败：battle_id不能为空"}
    if not question_type:
        return {"code": 40001, "message": "参数校验失败：question_type不能为空"}

    db = Database.get_instance()
    boss_repo = BossRepository(db)
    card_repo = CardRepository(db)
    battle_repo = BattleRecordRepository(db)

    boss = boss_repo.get_by_id(boss_id)
    if not boss:
        return {"code": 40403, "message": "Boss不存在"}

    battle = battle_repo.get_by_id(int(battle_id))
    if not battle:
        return {"code": 40404, "message": "战斗记录不存在"}

    is_weakness_card = battle.is_weakness_card
    correct_answer = battle.correct_answer or ""
    explanation = battle.explanation or ""
    score = None
    feedback = None
    improvement = None
    is_victory = False

    if question_type == "choice":
        is_victory = answer.strip().upper() == correct_answer.strip().upper()
    elif question_type == "short_answer":
        try:
            evaluator = AnswerEvaluator(db=db)
            eval_result = evaluator.evaluate(
                question=battle.question_content or "",
                user_answer=answer,
                correct_answer=correct_answer,
                question_type="简答题",
            )
            score = eval_result.get("score", 0)
            feedback = eval_result.get("feedback", "")
            improvement = eval_result.get("improvement", "")
            explanation = eval_result.get("explanation", explanation)
            is_victory = score >= 60
        except Exception:
            is_victory = False
            score = 0
            feedback = "AI评分服务异常"
    elif question_type == "leetcode":
        is_victory = bool(is_solved)
    else:
        return {"code": 40001, "message": "参数校验失败：不支持的question_type"}

    if is_victory and is_weakness_card:
        durability_change = 30
    elif is_victory:
        durability_change = 20
    else:
        durability_change = -5

    card = card_repo.get_by_id(battle.card_id)
    durability_after = None
    if card:
        new_durability = max(0, min(100, card.durability + durability_change))
        durability_after = new_durability
        card_repo.update(battle.card_id, durability=new_durability)

    battle_repo.update_result(
        record_id=int(battle_id),
        is_victory=is_victory,
        answer=answer,
        score=score if score is not None else 0,
        durability_change=durability_change,
        explanation=explanation,
    )

    guide_service = GuideService()
    npc_id_for_guide = boss.npc_id if boss else None
    has_available = _has_available_bosses(db)
    guide = guide_service.generate_guides(
        scene="after_boss",
        is_victory=is_victory,
        card_id=battle.card_id,
        npc_id=npc_id_for_guide,
        has_available_boss=has_available,
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "is_victory": is_victory,
            "durability_change": durability_change,
            "durability_after": durability_after,
            "is_weakness_card": is_weakness_card,
            "correct_answer": correct_answer if question_type != "leetcode" else None,
            "explanation": explanation,
            "score": score,
            "feedback": feedback,
            "improvement": improvement,
            "guide": guide.model_dump(),
        }
    }

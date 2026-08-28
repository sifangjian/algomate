import json
import logging
from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import desc

from algomate.data.database import Database
from algomate.models.cards import Card
from algomate.models.problem_card import ProblemCard
from algomate.models.solution_card import SolutionCard
from algomate.models.technique_card import TechniqueCard
from algomate.models.review_records import ReviewRecord
from algomate.config.algorithm_types import ALGORITHM_TYPES

router = APIRouter(prefix="/overview", tags=["主题概览"])
logger = logging.getLogger(__name__)


def _parse_tags(tags_json):
    if not tags_json:
        return []
    try:
        return json.loads(tags_json)
    except (json.JSONDecodeError, TypeError):
        return []


class TopicCard(BaseModel):
    key: str
    name: str
    problem_count: int = 0
    solution_count: int = 0
    technique_count: int = 0
    due_technique_count: int = 0
    critical_technique_count: int = 0


class OverviewResponse(BaseModel):
    topics: List[TopicCard]
    total_due: int
    total_critical: int
    total_problems: int
    total_solutions: int
    total_techniques: int


@router.get("", response_model=OverviewResponse)
def get_overview():
    """获取主题聚合数据，用于首页主题网格展示（按单个算法类型展示）"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        today = date.today()

        # 获取所有数据
        all_problems = session.query(ProblemCard).all()
        all_solutions = session.query(SolutionCard).all()
        all_techniques = session.query(TechniqueCard).all()

        # 构建每个算法类型的统计映射
        topic_stats = {}
        for algo_type in ALGORITHM_TYPES:
            topic_stats[algo_type] = {
                "name": algo_type,
                "problem_count": 0,
                "solution_count": 0,
                "technique_count": 0,
                "due_technique_count": 0,
                "critical_technique_count": 0,
            }

        # 统计题目到各算法类型（通过 tags 匹配算法类型名）
        # 注意：一道题目可能有多个算法类型标签，需要分别计入各类型的统计
        for p in all_problems:
            tags = _parse_tags(p.tags)
            for tag in tags:
                if tag in topic_stats:
                    topic_stats[tag]["problem_count"] += 1

        # 统计技巧到各算法类型（通过 Card 的 algorithm_type 匹配）
        for t in all_techniques:
            card = session.query(Card).filter(Card.id == t.card_id).first()
            if not card or not card.algorithm_type:
                continue
            algo_type = card.algorithm_type
            if algo_type in topic_stats:
                topic_stats[algo_type]["technique_count"] += 1
                if card.durability < 30:
                    topic_stats[algo_type]["critical_technique_count"] += 1
                elif card.next_review_date and card.next_review_date.date() <= today:
                    topic_stats[algo_type]["due_technique_count"] += 1

        # 整理返回
        topics = []
        total_due = 0
        total_critical = 0
        for algo_type in ALGORITHM_TYPES:
            stat = topic_stats[algo_type]
            topics.append(TopicCard(
                key=algo_type,
                name=stat["name"],
                problem_count=stat["problem_count"],
                solution_count=stat["solution_count"],
                technique_count=stat["technique_count"],
                due_technique_count=stat["due_technique_count"],
                critical_technique_count=stat["critical_technique_count"],
            ))
            total_due += stat["due_technique_count"]
            total_critical += stat["critical_technique_count"]

        # 有待复习的主题置顶，其余按技巧数量降序
        topics.sort(key=lambda t: (
            0 if t.due_technique_count > 0 or t.critical_technique_count > 0 else 1,
            -t.technique_count,
        ))

        return OverviewResponse(
            topics=topics,
            total_due=total_due,
            total_critical=total_critical,
            total_problems=len(all_problems),
            total_solutions=len(all_solutions),
            total_techniques=len(all_techniques),
        )
    finally:
        session.close()


class TopicDetailCard(BaseModel):
    id: int
    name: str
    card_type: str  # problem / solution / technique
    tags: List[str] = []
    difficulty: str = ""
    solution_count: int = 0
    review_status: str = "normal"
    problem_title: str = ""


class TopicDetailResponse(BaseModel):
    algorithm_type: str
    problems: List[TopicDetailCard] = []
    solutions: List[TopicDetailCard] = []
    techniques: List[TopicDetailCard] = []


class RecentActivity(BaseModel):
    time: str
    action: str
    target: str
    type: str  # technique / problem / solution / review


class RecentActivitiesResponse(BaseModel):
    activities: List[RecentActivity]


@router.get("/recent", response_model=RecentActivitiesResponse)
def get_recent_activities():
    """获取最近 5 条活动记录（新建技巧、新建题目、新建解法、复习完成）"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        activities: list[dict] = []

        # 技巧卡片
        for t in session.query(TechniqueCard).order_by(TechniqueCard.created_at.desc()).limit(10).all():
            activities.append({
                "_sort": t.created_at,
                "time": t.created_at.strftime("%H:%M"),
                "action": "新建技巧",
                "target": t.name,
                "type": "technique",
            })

        # 题目卡片
        for p in session.query(ProblemCard).order_by(ProblemCard.created_at.desc()).limit(10).all():
            activities.append({
                "_sort": p.created_at,
                "time": p.created_at.strftime("%H:%M"),
                "action": "新建题目",
                "target": p.title,
                "type": "problem",
            })

        # 解法卡片
        for s in session.query(SolutionCard).order_by(SolutionCard.created_at.desc()).limit(10).all():
            activities.append({
                "_sort": s.created_at,
                "time": s.created_at.strftime("%H:%M"),
                "action": "新建解法",
                "target": s.name,
                "type": "solution",
            })

        # 复习记录（已完成且有完成时间）
        for r in (
            session.query(ReviewRecord)
            .filter(ReviewRecord.status == "completed", ReviewRecord.completed_at.isnot(None))
            .order_by(ReviewRecord.completed_at.desc())
            .limit(10)
            .all()
        ):
            card_name = r.card.name if r.card else ""
            activities.append({
                "_sort": r.completed_at,
                "time": r.completed_at.strftime("%H:%M"),
                "action": "复习完成",
                "target": card_name,
                "type": "review",
            })

        # 按时间降序取前 5
        activities.sort(key=lambda a: a["_sort"], reverse=True)
        top5 = activities[:5]

        return RecentActivitiesResponse(
            activities=[RecentActivity(**a) for a in top5]
        )
    finally:
        session.close()


@router.get("/topic/{algorithm_type}", response_model=TopicDetailResponse)
def get_topic_detail(algorithm_type: str):
    """获取某个算法类型下的所有卡片（题目、解法、技巧）

    三种卡片独立按手动设置的算法类型匹配，无继承关系。
    """
    db = Database.get_instance()
    session = db.get_session()
    try:
        today = date.today()

        # 技巧卡片（通过 Card.algorithm_type 匹配）
        techniques = []
        for t in session.query(TechniqueCard).all():
            card = session.query(Card).filter(Card.id == t.card_id).first()
            if not card or card.algorithm_type != algorithm_type:
                continue
            review_status = "normal"
            if card.durability < 30:
                review_status = "critical"
            elif card.next_review_date and card.next_review_date.date() <= today:
                review_status = "due"
            techniques.append(TopicDetailCard(
                id=t.id,
                name=t.name,
                card_type="technique",
                review_status=review_status,
            ))

        # 题目卡片（通过手动 tags 匹配）
        problems = []
        for p in session.query(ProblemCard).all():
            tags = _parse_tags(p.tags)
            if algorithm_type not in tags:
                continue
            problems.append(TopicDetailCard(
                id=p.id,
                name=p.title,
                card_type="problem",
                tags=tags,
                difficulty=p.difficulty,
                solution_count=len(p.solutions) if p.solutions else 0,
            ))

        # 解法卡片（通过其关联技巧的 Card.algorithm_type 匹配）
        solutions = []
        for s in session.query(SolutionCard).all():
            matched = False
            for t in s.techniques:
                card = session.query(Card).filter(Card.id == t.card_id).first()
                if card and card.algorithm_type == algorithm_type:
                    matched = True
                    break
            if matched:
                solutions.append(TopicDetailCard(
                    id=s.id,
                    name=s.name,
                    card_type="solution",
                    problem_title=s.problem.title if s.problem else "",
                    solution_count=len(s.techniques) if s.techniques else 0,
                ))

        return TopicDetailResponse(
            algorithm_type=algorithm_type,
            problems=problems,
            solutions=solutions,
            techniques=techniques,
        )
    finally:
        session.close()


@router.get("/search")
def search_cards(
    keyword: str = Query(..., description="搜索关键词"),
):
    """统一搜索：根据关键词模糊匹配题目、解法、技巧的名称"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        kw = f"%{keyword}%"

        # 搜索题目
        problems = []
        for p in session.query(ProblemCard).filter(ProblemCard.title.ilike(kw)).all():
            problems.append({
                "id": p.id,
                "name": p.title,
                "card_type": "problem",
                "difficulty": p.difficulty,
            })

        # 搜索解法
        solutions = []
        for s in session.query(SolutionCard).filter(SolutionCard.name.ilike(kw)).all():
            solutions.append({
                "id": s.id,
                "name": s.name,
                "card_type": "solution",
                "problem_title": s.problem.title if s.problem else "",
            })

        # 搜索技巧
        techniques = []
        for t in session.query(TechniqueCard).filter(TechniqueCard.name.ilike(kw)).all():
            techniques.append({
                "id": t.id,
                "name": t.name,
                "card_type": "technique",
                "category": t.category,
            })

        return {
            "problems": problems,
            "solutions": solutions,
            "techniques": techniques,
        }
    finally:
        session.close()
import json
import logging
from datetime import date
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import desc

from algomate.data.database import Database
from algomate.models.cards import Card
from algomate.models.problem_card import ProblemCard
from algomate.models.solution_card import SolutionCard
from algomate.models.technique_card import TechniqueCard
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
        for p in all_problems:
            tags = _parse_tags(p.tags)
            for tag in tags:
                if tag in topic_stats:
                    topic_stats[tag]["problem_count"] += 1
                    break

        # 统计解法到各算法类型（通过题目 tags 匹配）
        for s in all_solutions:
            if s.problem and s.problem.tags:
                tags = _parse_tags(s.problem.tags)
                for tag in tags:
                    if tag in topic_stats:
                        topic_stats[tag]["solution_count"] += 1
                        break

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
    proficiency: int = 0
    algorithm_type: str = ""
    problem_title: str = ""


class TopicDetailResponse(BaseModel):
    algorithm_type: str
    problems: List[TopicDetailCard] = []
    solutions: List[TopicDetailCard] = []
    techniques: List[TopicDetailCard] = []


@router.get("/topic/{algorithm_type}", response_model=TopicDetailResponse)
def get_topic_detail(algorithm_type: str):
    """获取某个算法类型下的所有卡片（题目、解法、技巧）"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        today = date.today()

        # 技巧卡片
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
                proficiency=t.proficiency,
                algorithm_type=card.algorithm_type or "",
            ))

        # 题目卡片（通过 tags 匹配）
        problems = []
        problem_ids = set()
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
            problem_ids.add(p.id)

        # 解法卡片（通过关联的题目）
        solutions = []
        seen_solution_ids = set()
        for pid in problem_ids:
            p = session.query(ProblemCard).filter(ProblemCard.id == pid).first()
            if p and p.solutions:
                for s in p.solutions:
                    if s.id in seen_solution_ids:
                        continue
                    seen_solution_ids.add(s.id)
                    solutions.append(TopicDetailCard(
                        id=s.id,
                        name=s.name,
                        card_type="solution",
                        problem_title=p.title,
                        solution_count=len(s.techniques) if s.techniques else 0,
                    ))

        # 再补充：通过技巧关联的解法
        for t in session.query(TechniqueCard).all():
            card = session.query(Card).filter(Card.id == t.card_id).first()
            if not card or card.algorithm_type != algorithm_type:
                continue
            if t.solutions:
                for s in t.solutions:
                    if s.id in seen_solution_ids:
                        continue
                    seen_solution_ids.add(s.id)
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
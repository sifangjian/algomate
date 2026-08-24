import json
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc

from algomate.data.database import Database
from algomate.models.problem_card import ProblemCard, ProblemStatus

router = APIRouter(prefix="/problems", tags=["题目卡片"])
logger = logging.getLogger(__name__)


class ProblemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="题目全称，如 '645. 错误的集合'")
    difficulty: str = Field("medium", description="难度: easy/medium/hard")
    leetcode_link: str = Field("", description="原题链接")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    my_status: str = Field("untried", description="我的状态: untried/accepted/optimal")
    notes: str = Field("", description="注意事项")
    video_demo_link: str = Field("", description="视频演示链接")
    related_problem_ids: List[int] = Field(default_factory=list, description="关联题目ID列表")


class ProblemUpdate(BaseModel):
    title: Optional[str] = None
    difficulty: Optional[str] = None
    leetcode_link: Optional[str] = None
    tags: Optional[List[str]] = None
    my_status: Optional[str] = None
    notes: Optional[str] = None
    video_demo_link: Optional[str] = None
    related_problem_ids: Optional[List[int]] = None


class ProblemResponse(BaseModel):
    id: int
    title: str
    difficulty: str
    leetcode_link: str
    tags: List[str]
    my_status: str
    notes: str = ""
    video_demo_link: str = ""
    related_problem_ids: List[int] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    solution_count: int = 0

    class Config:
        from_attributes = True


class ProblemDetailResponse(ProblemResponse):
    solutions: List[dict] = []

    class Config:
        from_attributes = True


def _parse_tags(tags_json: Optional[str]) -> List[str]:
    if not tags_json:
        return []
    try:
        return json.loads(tags_json)
    except (json.JSONDecodeError, TypeError):
        return []


def _parse_related_ids(ids_json: Optional[str]) -> List[int]:
    if not ids_json:
        return []
    try:
        return json.loads(ids_json)
    except (json.JSONDecodeError, TypeError):
        return []


def _problem_to_response(p: ProblemCard) -> ProblemResponse:
    return ProblemResponse(
        id=p.id,
        title=p.title,
        difficulty=p.difficulty,
        leetcode_link=p.leetcode_link or "",
        tags=_parse_tags(p.tags),
        my_status=p.my_status,
        notes=p.notes or "",
        video_demo_link=p.video_demo_link or "",
        related_problem_ids=_parse_related_ids(p.related_problem_ids),
        created_at=p.created_at,
        updated_at=p.updated_at,
        solution_count=len(p.solutions) if hasattr(p, 'solutions') and p.solutions else 0,
    )


@router.post("", response_model=ProblemResponse)
def create_problem(data: ProblemCreate):
    db = Database.get_instance()
    session = db.get_session()
    try:
        problem = ProblemCard(
            title=data.title,
            difficulty=data.difficulty,
            leetcode_link=data.leetcode_link,
            tags=json.dumps(data.tags, ensure_ascii=False),
            my_status=data.my_status,
            notes=data.notes,
            video_demo_link=data.video_demo_link,
            related_problem_ids=json.dumps(data.related_problem_ids, ensure_ascii=False),
        )
        session.add(problem)
        session.commit()
        session.refresh(problem)
        logger.info(f"Created problem card: {problem.title} (id={problem.id})")
        return _problem_to_response(problem)
    finally:
        session.close()


@router.get("", response_model=List[ProblemResponse])
def list_problems(
    tags: Optional[str] = Query(None, description="按标签筛选，逗号分隔"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    difficulty: Optional[str] = Query(None, description="按难度筛选"),
):
    db = Database.get_instance()
    session = db.get_session()
    try:
        query = session.query(ProblemCard)

        if status:
            query = query.filter(ProblemCard.my_status == status)
        if difficulty:
            query = query.filter(ProblemCard.difficulty == difficulty)

        problems = query.order_by(desc(ProblemCard.created_at)).all()

        # 标签筛选（在内存中过滤，因为 tags 是 JSON 字段）
        if tags:
            filter_tags = [t.strip() for t in tags.split(",") if t.strip()]
            if filter_tags:
                problems = [
                    p for p in problems
                    if any(t in _parse_tags(p.tags) for t in filter_tags)
                ]

        return [_problem_to_response(p) for p in problems]
    finally:
        session.close()


@router.get("/search", response_model=List[ProblemResponse])
def search_problems(
    q: str = Query(..., min_length=1, description="搜索关键词"),
):
    """模糊搜索题目（按标题匹配）"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        kw = f"%{q}%"
        problems = (
            session.query(ProblemCard)
            .filter(ProblemCard.title.ilike(kw))
            .order_by(ProblemCard.title)
            .all()
        )
        return [_problem_to_response(p) for p in problems]
    finally:
        session.close()


@router.get("/{problem_id}", response_model=ProblemDetailResponse)
def get_problem(problem_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        problem = session.query(ProblemCard).filter(ProblemCard.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="题目卡片不存在")

        solutions = []
        if problem.solutions:
            for s in problem.solutions:
                techniques_list = []
                if s.techniques:
                    for tech in s.techniques:
                        techniques_list.append({
                            "id": tech.id,
                            "name": tech.name,
                            "category": tech.category,
                        })

                pitfalls_list = []
                if s.pitfalls:
                    try:
                        pitfalls_list = json.loads(s.pitfalls) if isinstance(s.pitfalls, str) else s.pitfalls
                    except (json.JSONDecodeError, TypeError):
                        pitfalls_list = []

                solutions.append({
                    "id": s.id,
                    "name": s.name,
                    "time_complexity": s.time_complexity or "",
                    "space_complexity": s.space_complexity or "",
                    "breakthrough": s.breakthrough or "",
                    "approach": s.approach or "",
                    "code": s.code or "",
                    "pitfalls": pitfalls_list,
                    "techniques": techniques_list,
                })

        return ProblemDetailResponse(
            id=problem.id,
            title=problem.title,
            difficulty=problem.difficulty,
            leetcode_link=problem.leetcode_link or "",
            tags=_parse_tags(problem.tags),
            my_status=problem.my_status,
            notes=problem.notes or "",
            video_demo_link=problem.video_demo_link or "",
            related_problem_ids=_parse_related_ids(problem.related_problem_ids),
            created_at=problem.created_at,
            updated_at=problem.updated_at,
            solution_count=len(problem.solutions) if problem.solutions else 0,
            solutions=solutions,
        )
    finally:
        session.close()


@router.put("/{problem_id}", response_model=ProblemResponse)
def update_problem(problem_id: int, data: ProblemUpdate):
    db = Database.get_instance()
    session = db.get_session()
    try:
        problem = session.query(ProblemCard).filter(ProblemCard.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="题目卡片不存在")

        update_data = data.model_dump(exclude_unset=True)
        if "tags" in update_data and update_data["tags"] is not None:
            update_data["tags"] = json.dumps(update_data["tags"], ensure_ascii=False)
        if "related_problem_ids" in update_data and update_data["related_problem_ids"] is not None:
            update_data["related_problem_ids"] = json.dumps(update_data["related_problem_ids"], ensure_ascii=False)

        for key, value in update_data.items():
            setattr(problem, key, value)

        problem.updated_at = datetime.now()
        session.commit()
        session.refresh(problem)
        logger.info(f"Updated problem card: {problem.title} (id={problem.id})")
        return _problem_to_response(problem)
    finally:
        session.close()


@router.delete("/{problem_id}")
def delete_problem(problem_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        problem = session.query(ProblemCard).filter(ProblemCard.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="题目卡片不存在")

        session.delete(problem)
        session.commit()
        logger.info(f"Deleted problem card: {problem.title} (id={problem.id})")
        return {"message": "删除成功"}
    finally:
        session.close()
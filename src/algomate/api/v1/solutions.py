import json
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc

from algomate.data.database import Database
from algomate.models.activity_log import ActivityLog
from algomate.models.solution_card import SolutionCard
from algomate.models.solution_technique import SolutionTechnique

router = APIRouter(prefix="/solutions", tags=["解法卡片"])
logger = logging.getLogger(__name__)


class SolutionCreate(BaseModel):
    problem_id: int = Field(..., description="关联的题目 ID")
    name: str = Field(..., min_length=1, max_length=200, description="解法名称")
    language: str = Field("", description="编程语言，如 python/javascript/cpp")
    is_optimal: int = Field(0, ge=0, le=1, description="是否最优解: 0/1")
    time_complexity: str = Field("", description="时间复杂度")
    space_complexity: str = Field("", description="空间复杂度")
    breakthrough: str = Field("", description="突破口")
    approach: str = Field("", description="详细思路 Markdown")
    code: str = Field("", description="代码块")
    pitfalls: List[str] = Field(default_factory=list, description="易错点列表")


class SolutionUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    is_optimal: Optional[int] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    breakthrough: Optional[str] = None
    approach: Optional[str] = None
    code: Optional[str] = None
    pitfalls: Optional[List[str]] = None


class SolutionResponse(BaseModel):
    id: int
    problem_id: int
    name: str
    language: str = ""
    is_optimal: int = 0
    time_complexity: str
    space_complexity: str
    breakthrough: str
    approach: str
    code: str
    pitfalls: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    technique_count: int = 0
    problem_title: str = ""

    class Config:
        from_attributes = True


class SolutionDetailResponse(SolutionResponse):
    techniques: List[dict] = []

    class Config:
        from_attributes = True


def _parse_pitfalls(pitfalls_json: Optional[str]) -> List[str]:
    if not pitfalls_json:
        return []
    try:
        return json.loads(pitfalls_json)
    except (json.JSONDecodeError, TypeError):
        return []


def _solution_to_response(s: SolutionCard) -> SolutionResponse:
    return SolutionResponse(
        id=s.id,
        problem_id=s.problem_id,
        name=s.name,
        language=s.language or "",
        is_optimal=s.is_optimal or 0,
        time_complexity=s.time_complexity or "",
        space_complexity=s.space_complexity or "",
        breakthrough=s.breakthrough or "",
        approach=s.approach or "",
        code=s.code or "",
        pitfalls=_parse_pitfalls(s.pitfalls),
        created_at=s.created_at,
        updated_at=s.updated_at,
        technique_count=len(s.techniques) if s.techniques else 0,
        problem_title=s.problem.title if s.problem else "",
    )


@router.post("", response_model=SolutionResponse)
def create_solution(data: SolutionCreate):
    db = Database.get_instance()
    session = db.get_session()
    try:
        # 验证关联题目存在
        from algomate.models.problem_card import ProblemCard
        problem = session.query(ProblemCard).filter(ProblemCard.id == data.problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="关联的题目卡片不存在")

        solution = SolutionCard(
            problem_id=data.problem_id,
            name=data.name,
            language=data.language,
            is_optimal=data.is_optimal,
            time_complexity=data.time_complexity,
            space_complexity=data.space_complexity,
            breakthrough=data.breakthrough,
            approach=data.approach,
            code=data.code,
            pitfalls=json.dumps(data.pitfalls, ensure_ascii=False),
        )
        session.add(solution)
        session.commit()
        session.refresh(solution)

        log_entry = ActivityLog(
            type="auto_create",
            card_type="solution",
            card_name=solution.name,
            card_id=solution.id,
            content=f"创建解法卡片: {solution.name}",
        )
        session.add(log_entry)
        session.commit()

        logger.info(f"Created solution card: {solution.name} (id={solution.id})")
        return _solution_to_response(solution)
    finally:
        session.close()


@router.get("", response_model=List[SolutionResponse])
def list_solutions():
    db = Database.get_instance()
    session = db.get_session()
    try:
        solutions = session.query(SolutionCard).order_by(desc(SolutionCard.created_at)).all()
        return [_solution_to_response(s) for s in solutions]
    finally:
        session.close()


@router.get("/{solution_id}", response_model=SolutionDetailResponse)
def get_solution(solution_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        solution = session.query(SolutionCard).filter(SolutionCard.id == solution_id).first()
        if not solution:
            raise HTTPException(status_code=404, detail="解法卡片不存在")

        techniques = []
        if solution.techniques:
            for t in solution.techniques:
                from algomate.models.cards import Card
                card = session.query(Card).filter(Card.id == t.card_id).first()
                review_status = "normal"
                if card:
                    if card.durability < 30:
                        review_status = "critical"
                    elif card.next_review_date and card.next_review_date.date() <= datetime.now().date():
                        review_status = "due"

                techniques.append({
                    "id": t.id,
                    "name": t.name,
                    "review_status": review_status,
                })

        return SolutionDetailResponse(
            id=solution.id,
            problem_id=solution.problem_id,
            name=solution.name,
            language=solution.language or "",
            is_optimal=solution.is_optimal or 0,
            time_complexity=solution.time_complexity or "",
            space_complexity=solution.space_complexity or "",
            breakthrough=solution.breakthrough or "",
            approach=solution.approach or "",
            code=solution.code or "",
            pitfalls=_parse_pitfalls(solution.pitfalls),
            created_at=solution.created_at,
            updated_at=solution.updated_at,
            technique_count=len(solution.techniques) if solution.techniques else 0,
            problem_title=solution.problem.title if solution.problem else "",
            techniques=techniques,
        )
    finally:
        session.close()


@router.put("/{solution_id}", response_model=SolutionResponse)
def update_solution(solution_id: int, data: SolutionUpdate):
    db = Database.get_instance()
    session = db.get_session()
    try:
        solution = session.query(SolutionCard).filter(SolutionCard.id == solution_id).first()
        if not solution:
            raise HTTPException(status_code=404, detail="解法卡片不存在")

        update_data = data.model_dump(exclude_unset=True)
        if "pitfalls" in update_data and update_data["pitfalls"] is not None:
            update_data["pitfalls"] = json.dumps(update_data["pitfalls"], ensure_ascii=False)

        changed_fields = {}
        for key, value in update_data.items():
            old_val = getattr(solution, key)
            if old_val != value:
                changed_fields[key] = {"old": old_val, "new": value}

        for key, value in update_data.items():
            setattr(solution, key, value)

        solution.updated_at = datetime.now()
        session.commit()
        session.refresh(solution)

        if changed_fields:
            log_entry = ActivityLog(
                type="auto_update",
                card_type="solution",
                card_name=solution.name,
                card_id=solution.id,
                content=f"修改解法卡片: {solution.name}",
                details={"changed_fields": changed_fields},
            )
            session.add(log_entry)
            session.commit()

        logger.info(f"Updated solution card: {solution.name} (id={solution.id})")
        return _solution_to_response(solution)
    finally:
        session.close()


@router.delete("/{solution_id}")
def delete_solution(solution_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        solution = session.query(SolutionCard).filter(SolutionCard.id == solution_id).first()
        if not solution:
            raise HTTPException(status_code=404, detail="解法卡片不存在")

        session.delete(solution)
        session.commit()
        logger.info(f"Deleted solution card: {solution.name} (id={solution.id})")
        return {"message": "删除成功"}
    finally:
        session.close()


# --- 关联技巧 ---

class LinkTechniqueRequest(BaseModel):
    technique_id: int = Field(..., description="技巧卡片 ID")


@router.post("/{solution_id}/techniques", response_model=SolutionDetailResponse)
def link_technique(solution_id: int, data: LinkTechniqueRequest):
    db = Database.get_instance()
    session = db.get_session()
    try:
        solution = session.query(SolutionCard).filter(SolutionCard.id == solution_id).first()
        if not solution:
            raise HTTPException(status_code=404, detail="解法卡片不存在")

        from algomate.models.technique_card import TechniqueCard
        technique = session.query(TechniqueCard).filter(TechniqueCard.id == data.technique_id).first()
        if not technique:
            raise HTTPException(status_code=404, detail="技巧卡片不存在")

        # 检查是否已关联
        existing = session.query(SolutionTechnique).filter(
            SolutionTechnique.solution_id == solution_id,
            SolutionTechnique.technique_id == data.technique_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="已关联该技巧")

        st = SolutionTechnique(solution_id=solution_id, technique_id=data.technique_id)
        session.add(st)
        session.commit()
        logger.info(f"Linked technique {data.technique_id} to solution {solution_id}")

        # 返回完整详情
        session.refresh(solution)
        techniques = []
        if solution.techniques:
            for t in solution.techniques:
                techniques.append({"id": t.id, "name": t.name})

        return SolutionDetailResponse(
            id=solution.id,
            problem_id=solution.problem_id,
            name=solution.name,
            language=solution.language or "",
            is_optimal=solution.is_optimal or 0,
            time_complexity=solution.time_complexity or "",
            space_complexity=solution.space_complexity or "",
            breakthrough=solution.breakthrough or "",
            approach=solution.approach or "",
            code=solution.code or "",
            pitfalls=_parse_pitfalls(solution.pitfalls),
            created_at=solution.created_at,
            updated_at=solution.updated_at,
            technique_count=len(solution.techniques) if solution.techniques else 0,
            problem_title=solution.problem.title if solution.problem else "",
            techniques=techniques,
        )
    finally:
        session.close()


@router.delete("/{solution_id}/techniques/{technique_id}")
def unlink_technique(solution_id: int, technique_id: int):
    db = Database.get_instance()
    session = db.get_session()
    try:
        st = session.query(SolutionTechnique).filter(
            SolutionTechnique.solution_id == solution_id,
            SolutionTechnique.technique_id == technique_id,
        ).first()
        if not st:
            raise HTTPException(status_code=404, detail="未找到关联关系")

        session.delete(st)
        session.commit()
        logger.info(f"Unlinked technique {technique_id} from solution {solution_id}")
        return {"message": "解除关联成功"}
    finally:
        session.close()


# --- 反向链接：解法关联的技巧 ---
@router.get("/{solution_id}/backlinks")
def get_solution_backlinks(solution_id: int):
    """查询引用了该解法的技巧（本质上是解法关联的技巧列表）"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        solution = session.query(SolutionCard).filter(SolutionCard.id == solution_id).first()
        if not solution:
            raise HTTPException(status_code=404, detail="解法卡片不存在")

        techniques = []
        if solution.techniques:
            for t in solution.techniques:
                techniques.append({
                    "id": t.id,
                    "name": t.name,
                })

        return {"techniques": techniques}
    finally:
        session.close()
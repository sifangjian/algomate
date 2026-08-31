import json
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc

from algomate.data.database import Database
from algomate.models.activity_log import ActivityLog
from algomate.models.problem_card import ProblemCard

router = APIRouter(prefix="/problems", tags=["题目卡片"])
logger = logging.getLogger(__name__)


class ProblemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="题目全称，如 '645. 错误的集合'")
    leetcode_slug: Optional[str] = Field(None, description="LeetCode 题目唯一标识(slug)，用于一键导入去重与变体题关联")
    difficulty: str = Field("medium", description="难度: easy/medium/hard")
    leetcode_link: str = Field("", description="原题链接")
    tags: List[str] = Field(default_factory=list, description="标签列表（LeetCode 算法分类属性）")
    breakthrough: str = Field("", description="突破口：本题要解决的核心问题")
    is_optimal: int = Field(0, ge=0, le=1, description="是否已有最优解: 0/1")
    variants: List[str] = Field(default_factory=list, description="同考点变体题 slug 列表")
    video_demo_link: str = Field("", description="视频演示链接")
    related_problem_ids: List[int] = Field(default_factory=list, description="关联题目ID列表")


class ProblemUpdate(BaseModel):
    title: Optional[str] = None
    difficulty: Optional[str] = None
    leetcode_link: Optional[str] = None
    tags: Optional[List[str]] = None
    breakthrough: Optional[str] = None
    is_optimal: Optional[int] = None
    variants: Optional[List[str]] = None
    video_demo_link: Optional[str] = None
    related_problem_ids: Optional[List[int]] = None


class ProblemResponse(BaseModel):
    id: int
    title: str
    leetcode_slug: Optional[str] = None
    difficulty: str
    leetcode_link: str = ""
    tags: List[str]
    breakthrough: str = ""
    is_optimal: int = 0
    variants: List[str] = []
    video_demo_link: str = ""
    related_problem_ids: List[int] = []
    card_id: Optional[int] = None
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
        leetcode_slug=p.leetcode_slug,
        difficulty=p.difficulty,
        leetcode_link=p.leetcode_link or "",
        tags=_parse_tags(p.tags),
        breakthrough=p.breakthrough or "",
        is_optimal=p.is_optimal or 0,
        variants=_parse_tags(p.variants),
        video_demo_link=p.video_demo_link or "",
        related_problem_ids=_parse_related_ids(p.related_problem_ids),
        card_id=p.card_id,
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
            leetcode_slug=data.leetcode_slug,
            difficulty=data.difficulty,
            leetcode_link=data.leetcode_link,
            tags=json.dumps(data.tags, ensure_ascii=False),
            breakthrough=data.breakthrough,
            is_optimal=data.is_optimal,
            variants=json.dumps(data.variants, ensure_ascii=False),
            related_problem_ids=json.dumps(data.related_problem_ids, ensure_ascii=False),
        )
        session.add(problem)
        session.commit()
        session.refresh(problem)

        log_entry = ActivityLog(
            type="auto_create",
            card_type="problem",
            card_name=problem.title,
            card_id=problem.id,
            content=f"创建题目卡片: {problem.title}",
        )
        session.add(log_entry)
        session.commit()

        logger.info(f"Created problem card: {problem.title} (id={problem.id})")
        return _problem_to_response(problem)
    finally:
        session.close()


@router.get("", response_model=List[ProblemResponse])
def list_problems(
    tags: Optional[str] = Query(None, description="按标签筛选，逗号分隔"),
    difficulty: Optional[str] = Query(None, description="按难度筛选"),
):
    db = Database.get_instance()
    session = db.get_session()
    try:
        query = session.query(ProblemCard)

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
        return ProblemDetailResponse(**_build_problem_detail(problem))
    finally:
        session.close()


@router.get("/by-slug/{slug}", response_model=ProblemDetailResponse)
def get_problem_by_slug(slug: str):
    """按 LeetCode slug 查题目详情（插件重做时加载系统已存信息用）"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        problem = session.query(ProblemCard).filter(ProblemCard.leetcode_slug == slug).first()
        if not problem:
            raise HTTPException(status_code=404, detail="系统中暂无该题")
        return ProblemDetailResponse(**_build_problem_detail(problem))
    finally:
        session.close()


def _build_problem_detail(problem: ProblemCard) -> dict:
    """构建题目详情（含解法与技巧卡完整信息），/problems/{id} 与 /problems/by-slug/{slug} 共用"""
    solutions = []
    if problem.solutions:
        for s in problem.solutions:
            techniques_list = []
            if s.techniques:
                for tech in s.techniques:
                    techniques_list.append({
                        "id": tech.id,
                        "name": tech.name,
                        "use_cases": tech.use_cases or "",
                        "notes": tech.notes or "",
                        "code_template": tech.code_template or "",
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
                "language": s.language or "",
                "is_optimal": s.is_optimal or 0,
                "time_complexity": s.time_complexity or "",
                "space_complexity": s.space_complexity or "",
                "notes": s.notes or "",
                "approach": s.approach or "",
                "code": s.code or "",
                "pitfalls": pitfalls_list,
                "techniques": techniques_list,
            })

    return {
        "id": problem.id,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "leetcode_link": problem.leetcode_link or "",
        "tags": _parse_tags(problem.tags),
        "breakthrough": problem.breakthrough or "",
        "is_optimal": problem.is_optimal or 0,
        "variants": _parse_tags(problem.variants),
        "video_demo_link": problem.video_demo_link or "",
        "related_problem_ids": _parse_related_ids(problem.related_problem_ids),
        "card_id": problem.card_id,
        "created_at": problem.created_at,
        "updated_at": problem.updated_at,
        "solution_count": len(problem.solutions) if problem.solutions else 0,
        "solutions": solutions,
    }


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

        changed_fields = {}
        for key, value in update_data.items():
            old_val = getattr(problem, key)
            if old_val != value:
                changed_fields[key] = {"old": old_val, "new": value}

        for key, value in update_data.items():
            setattr(problem, key, value)

        problem.updated_at = datetime.now()
        session.commit()
        session.refresh(problem)

        if changed_fields:
            log_entry = ActivityLog(
                type="auto_update",
                card_type="problem",
                card_name=problem.title,
                card_id=problem.id,
                content=f"修改题目卡片: {problem.title}",
                details={"changed_fields": changed_fields},
            )
            session.add(log_entry)
            session.commit()

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

        # 题卡作为修炼主单元时挂有一张复习卡(Card)，需一并删除，否则孤儿 Card 仍被算入待复习
        if problem.card_id:
            from algomate.models.cards import Card
            review_card = session.query(Card).filter(Card.id == problem.card_id).first()
            if review_card:
                session.delete(review_card)

        session.delete(problem)
        session.commit()
        logger.info(f"Deleted problem card: {problem.title} (id={problem.id})")
        return {"message": "删除成功"}
    finally:
        session.close()


class VariantPracticeRequest(BaseModel):
    variant_slugs: List[str] = Field(default_factory=list, description="本次练习覆盖的变体题 slug 列表")
    note: str = Field("", description="练习笔记")


@router.get("/{problem_id}/variant-set")
def get_variant_set(problem_id: int):
    """聚合变体题练习集（变体题复习法）：主问题 + 各 variant slug 的系统内状态"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        problem = session.query(ProblemCard).filter(ProblemCard.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="题目卡片不存在")

        variant_slugs = _parse_tags(problem.variants)
        items = []
        for v in variant_slugs:
            vp = session.query(ProblemCard).filter(ProblemCard.leetcode_slug == v).first()
            if vp:
                items.append({
                    "slug": v,
                    "in_system": True,
                    "problem_id": vp.id,
                    "title": vp.title,
                    "difficulty": vp.difficulty,
                    "solution_count": len(vp.solutions) if vp.solutions else 0,
                    "leetcode_link": vp.leetcode_link or f"https://leetcode.cn/problems/{v}/",
                })
            else:
                items.append({
                    "slug": v,
                    "in_system": False,
                    "problem_id": None,
                    "title": None,
                    "difficulty": None,
                    "solution_count": 0,
                    "leetcode_link": f"https://leetcode.cn/problems/{v}/",
                })

        return {
            "problem_id": problem.id,
            "title": problem.title,
            "slug": problem.leetcode_slug,
            "leetcode_link": problem.leetcode_link or "",
            "variants": items,
            "total": len(items) + 1,
        }
    finally:
        session.close()


@router.post("/{problem_id}/variant-practice")
def record_variant_practice(problem_id: int, data: VariantPracticeRequest):
    """记录一次变体题练习（聚合复习法），写入活动日志供复习追溯"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        problem = session.query(ProblemCard).filter(ProblemCard.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="题目卡片不存在")

        log_entry = ActivityLog(
            type="variant_practice",
            card_type="problem",
            card_id=problem.id,
            card_name=problem.title,
            content=f"变体题练习: {problem.title}",
            details={
                "variant_slugs": data.variant_slugs,
                "variant_count": len(data.variant_slugs),
                "note": data.note,
            },
        )
        session.add(log_entry)
        session.commit()
        session.refresh(log_entry)

        logger.info(f"Recorded variant practice for problem {problem.title} (id={problem.id})")
        return {
            "id": log_entry.id,
            "type": log_entry.type,
            "card_id": log_entry.card_id,
            "content": log_entry.content,
            "details": log_entry.details,
            "created_at": log_entry.created_at.isoformat() if log_entry.created_at else None,
        }
    finally:
        session.close()


class VariantUpdateRequest(BaseModel):
    variants: List[str] = Field(default_factory=list, description="同考点变体题 slug 列表（手动维护，逗号分隔输入请以数组传入）")


@router.put("/{problem_id}/variants")
def update_variants(problem_id: int, data: VariantUpdateRequest):
    """更新题卡的变体题列表（在题卡详情页手动维护，不依赖导入时填写）"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        problem = session.query(ProblemCard).filter(ProblemCard.id == problem_id).first()
        if not problem:
            raise HTTPException(status_code=404, detail="题目卡片不存在")
        # 去重保序
        seen = set()
        cleaned = []
        for v in data.variants:
            v = (v or "").strip()
            if v and v not in seen:
                seen.add(v)
                cleaned.append(v)
        problem.variants = json.dumps(cleaned, ensure_ascii=False)
        session.commit()
        return {
            "problem_id": problem.id,
            "variants": cleaned,
        }
    finally:
        session.close()


@router.get("/{problem_id}/review-notes")
def get_problem_review_notes(problem_id: int, limit: int = 10):
    """模块E: 返回该题卡复习卡的历史复习笔记(ReviewRecord.note)。

    用于题卡详情页展示「最近复习/重做时记录的边界遗漏与注意点」。
    """
    from algomate.models.cards import Card
    from algomate.models.review_records import ReviewRecord
    db = Database.get_instance()
    session = db.get_session()
    try:
        problem = session.query(ProblemCard).filter(ProblemCard.id == problem_id).first()
        if not problem or not problem.card_id:
            return {"problem_id": problem_id, "notes": []}
        records = (
            session.query(ReviewRecord)
            .filter(ReviewRecord.card_id == problem.card_id)
            .filter(ReviewRecord.note.isnot(None))
            .filter(ReviewRecord.note != "")
            .order_by(desc(ReviewRecord.id))
            .limit(limit)
            .all()
        )
        notes = [
            {
                "review_type": r.review_type,
                "note": r.note,
                "durability_after": r.durability_after,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in records
        ]
        return {"problem_id": problem_id, "notes": notes}
    except Exception as e:
        logger.error("get_problem_review_notes failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询复习笔记失败: {str(e)}")
    finally:
        session.close()

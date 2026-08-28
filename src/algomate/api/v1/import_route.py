"""LeetCode 一键导入路由

浏览器扩展在 LeetCode 题目页抓取题面/难度/标签/用户提交的代码后，
调用本接口自动建卡：题卡 + 解法卡（可选 + 技巧卡）。

分工原则（hard rule）：
- 系统只负责搬运结构化数据建卡壳：题目信息、难度、标签（作为算法分类属性）、代码。
- 心得体会、技巧总结由用户本人手动写，系统不替用户"总结技巧"。

去重与冲突处理：
- 题卡以 LeetCode slug 为唯一键。
- 同一题重复导入时：
  - 若已存在「code + language 完全相同」的解法 → 视为重复导入，返回 already_exists，
    不再新建（避免重复卡壳）。
  - 若已存在该题但解法不同 → 返回 conflict=True 与已有解法列表，由前端让用户选择
    「更新某条已有解法」或「新增一条解法」。
- 前端可传 update_solution_id 显式指定要更新的解法（覆盖其 code/语言/突破口/复杂度/易错点）。
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from algomate.data.database import Database
from algomate.models.activity_log import ActivityLog
from algomate.models.problem_card import ProblemCard
from algomate.models.solution_card import SolutionCard
from algomate.models.solution_technique import SolutionTechnique
from algomate.models.technique_card import TechniqueCard
from algomate.models.cards import Card

router = APIRouter(prefix="/import", tags=["LeetCode 导入"])
logger = logging.getLogger(__name__)


class TechniqueItem(BaseModel):
    """用户从一道题里手动提炼的一条技巧（可迁移的原子经验）"""
    name: str = Field(..., min_length=1, max_length=200, description="技巧名称（用户提炼，如 '哈希表存差值'）")
    summary: str = Field("", description="技巧总结/内容（用户提炼，可空）")
    code_template: str = Field("", description="技巧标准代码模板（可选）")


class ImportRequest(BaseModel):
    """从 LeetCode 导入一条题目所需的全部信息"""
    slug: str = Field(..., min_length=1, description="LeetCode 题目唯一标识(slug)，去重键")
    title: str = Field(..., min_length=1, max_length=200, description="题目全称，如 '645. 错误的集合'")
    difficulty: str = Field("medium", description="难度: easy/medium/hard")
    description: str = Field("", description="题目/解法描述 Markdown（系统搬运，用户无需关注）")
    leetcode_link: str = Field("", description="原题链接（深链）")
    tags: List[str] = Field(
        default_factory=list,
        description="题目标签（LeetCode topic tags），作为题卡的算法分类属性，不自动建技巧卡",
    )
    code: str = Field("", description="用户提交的代码（系统搬运）")
    language: str = Field("", description="编程语言，如 python/javascript/cpp")
    notes: str = Field("", description="破题思路（用户手动写，不搬运）")
    # 解法维度（用户做完题后填写，理解最清晰）
    breakthrough: str = Field("", description="突破口（针对本解法的具体切入）")
    time_complexity: str = Field("", description="时间复杂度，如 O(n)")
    space_complexity: str = Field("", description="空间复杂度，如 O(1)")
    pitfalls: List[str] = Field(default_factory=list, description="易错点列表（每行一条）")
    # 题目维度（手动补充）
    variants: List[str] = Field(default_factory=list, description="同考点变体题 slug 列表（手动填）")
    # 技巧卡（每条→一张，关联本解法）
    techniques: List[TechniqueItem] = Field(
        default_factory=list,
        description="用户手动提炼的技巧卡（每条→一张技巧卡并关联本解法），系统不自动生成",
    )
    # 冲突处理：显式指定要更新的已有解法 ID（覆盖式更新）
    update_solution_id: Optional[int] = Field(
        None, description="若与已有解法冲突且用户选择更新，则传此 ID 覆盖该解法"
    )


class ImportResponse(BaseModel):
    problem_id: int
    solution_id: int
    technique_ids: List[int] = []
    is_new_problem: bool = True
    existing_solution_count: int = 0
    already_exists: bool = False
    conflict: bool = False
    existing_solutions: List[dict] = []
    message: str = ""


def _create_user_technique(session, name: str, summary: str, code_template: str = "") -> TechniqueCard:
    """由用户手动提炼的内容创建一张技巧卡，并同步创建 Card 复习记录。

    与 techniques.py 的 create_technique 保持一致的建卡约定，确保遗忘曲线机制正确接入。
    """
    review_card = Card(
        name=name,
        difficulty=3,
        durability=80,
        review_level=0,
        card_type="tip",
        content=json.dumps({"summary": summary}, ensure_ascii=False),
    )
    session.add(review_card)
    session.flush()

    technique = TechniqueCard(
        card_id=review_card.id,
        name=name,
        use_cases=summary,
        code_template=code_template or "",
        memory_anchors="",
        notes=summary,
        video_demo_link="",
    )
    session.add(technique)
    session.flush()
    return technique


def _norm_lang(lang: str) -> str:
    """语言别名归一化，避免 python3/python、js/javascript 被当成不同解法。"""
    m = {
        "python3": "python", "py3": "python", "py": "python",
        "javascript": "javascript", "js": "javascript",
        "typescript": "typescript", "ts": "typescript",
        "c++": "cpp", "cpp": "cpp", "c": "c",
        "golang": "go", "go": "go",
        "mysql": "mysql", "sql": "sql",
        "java": "java", "rust": "rust", "kotlin": "kotlin", "scala": "scala", "swift": "swift",
    }
    return m.get((lang or "").strip().lower(), (lang or "").strip().lower())


def _norm_code(code: str) -> str:
    """代码归一化：去首尾空白、统一行尾，用于判断「相同解法」。"""
    return "\n".join((code or "").split()).strip()


def _build_solution_fields(data: ImportRequest) -> dict:
    """从请求构造解法卡的字段字典（新建与更新共用）。"""
    return dict(
        name=f"我的解法（{data.language or '代码'}）",
        language=data.language,
        code=data.code,
        approach=data.description,  # 系统搬运题面/思路描述，用户可改写
        time_complexity=data.time_complexity or "",
        space_complexity=data.space_complexity or "",
        breakthrough=data.breakthrough or "",
        pitfalls=json.dumps(data.pitfalls or [], ensure_ascii=False),
    )


@router.post("", response_model=ImportResponse)
def import_from_leetcode(data: ImportRequest):
    db = Database.get_instance()
    session = db.get_session()
    try:
        # 1. 按 slug 去重建题卡
        existing = (
            session.query(ProblemCard)
            .filter(ProblemCard.leetcode_slug == data.slug)
            .first()
        )

        is_new_problem = existing is None
        if existing:
            problem = existing
            if data.notes:
                problem.notes = data.notes
            if data.variants:
                problem.variants = json.dumps(data.variants, ensure_ascii=False)
            # 标签作为算法分类属性，重复导入时同步刷新
            problem.tags = json.dumps(data.tags, ensure_ascii=False)
        else:
            problem = ProblemCard(
                title=data.title,
                leetcode_slug=data.slug,
                difficulty=data.difficulty,
                leetcode_link=data.leetcode_link,
                tags=json.dumps(data.tags, ensure_ascii=False),
                notes=data.notes,
                variants=json.dumps(data.variants, ensure_ascii=False),
            )
            session.add(problem)
            session.flush()

            log_entry = ActivityLog(
                type="auto_create",
                card_type="problem",
                card_name=problem.title,
                card_id=problem.id,
                content=f"从 LeetCode 导入题目卡片: {problem.title}",
            )
            session.add(log_entry)

        # 2. 查同题已有解法，做去重/冲突判断
        existing_solutions = (
            session.query(SolutionCard)
            .filter(SolutionCard.problem_id == problem.id)
            .all()
        )

        # 完全相同解法（code + language 归一化后一致）=> 视为重复导入
        dup = None
        norm_code = _norm_code(data.code)
        norm_lang = _norm_lang(data.language)
        for sol in existing_solutions:
            if _norm_code(sol.code or "") == norm_code and _norm_lang(sol.language or "") == norm_lang:
                dup = sol
                break

        # 显式更新模式：覆盖指定解法
        if data.update_solution_id is not None:
            target = next((s for s in existing_solutions if s.id == data.update_solution_id), None)
            if not target:
                raise HTTPException(status_code=404, detail=f"未找到要更新的解法 ID={data.update_solution_id}")
            for k, v in _build_solution_fields(data).items():
                setattr(target, k, v)
            session.flush()
            solution = target
            technique_ids = _sync_techniques(session, solution, data.techniques)
            session.commit()
            session.refresh(problem)
            session.refresh(solution)
            return ImportResponse(
                problem_id=problem.id,
                solution_id=solution.id,
                technique_ids=technique_ids,
                is_new_problem=is_new_problem,
                existing_solution_count=len(existing_solutions),
                message="已更新指定解法",
            )

        # 重复导入：已存在完全相同解法
        if dup is not None:
            return ImportResponse(
                problem_id=problem.id,
                solution_id=dup.id,
                technique_ids=[],
                is_new_problem=is_new_problem,
                existing_solution_count=len(existing_solutions),
                already_exists=True,
                message="已存在相同解法（代码与语言一致），未重复创建",
            )

        # 同题存在其他不同解法 => 冲突，交由前端选择（除非本次是新建题，直接建）
        if existing_solutions:
            return ImportResponse(
                problem_id=problem.id,
                solution_id=0,
                technique_ids=[],
                is_new_problem=is_new_problem,
                existing_solution_count=len(existing_solutions),
                conflict=True,
                existing_solutions=[
                    {"id": s.id, "name": s.name, "language": s.language, "breakthrough": s.breakthrough}
                    for s in existing_solutions
                ],
                message="该题已有其他解法，请选择更新某条或新增一条",
            )

        # 3. 正常新建解法卡
        solution = SolutionCard(problem_id=problem.id, **_build_solution_fields(data))
        session.add(solution)
        session.flush()

        technique_ids = _sync_techniques(session, solution, data.techniques)

        session.commit()
        session.refresh(problem)
        session.refresh(solution)

        msg = "导入成功：新建题目卡与解法卡" if is_new_problem else "已存在该题：新建一条新解法"
        logger.info(f"LeetCode import (slug={data.slug}): problem_id={problem.id}, solution_id={solution.id}, techniques={technique_ids}")

        return ImportResponse(
            problem_id=problem.id,
            solution_id=solution.id,
            technique_ids=technique_ids,
            is_new_problem=is_new_problem,
            existing_solution_count=len(existing_solutions),
            message=msg,
        )
    finally:
        session.close()


def _sync_techniques(session, solution, techniques: List[TechniqueItem]) -> List[int]:
    """为解法关联用户手动提炼的技巧卡（每条→一张，去重）。"""
    technique_ids: List[int] = []
    seen_names = set()
    for item in techniques:
        name = item.name.strip()
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        technique = _create_user_technique(
            session, name=name, summary=item.summary.strip(), code_template=item.code_template.strip()
        )
        session.add(SolutionTechnique(solution_id=solution.id, technique_id=technique.id))
        technique_ids.append(technique.id)
        session.add(ActivityLog(
            type="manual_note",
            card_type="technique",
            card_name=technique.name,
            card_id=technique.id,
            content=f"用户导入时手动提炼技巧卡: {technique.name}",
        ))
    return technique_ids

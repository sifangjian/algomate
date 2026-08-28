"""LeetCode 一键导入路由

浏览器扩展在 LeetCode 页面抓取题面/难度/标签/用户提交的代码后，
调用本接口自动建卡：题卡 + 解法卡。

分工原则（hard rule）：
- 系统只负责搬运结构化数据建卡壳：题目信息、难度、标签（作为算法分类属性）、代码。
- 心得体会、技巧总结由用户本人手动写，系统不替用户"总结技巧"。

去重：题卡以 LeetCode slug 为唯一键；同一题重复导入 = 追加一条新解法。
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
    techniques: List[TechniqueItem] = Field(
        default_factory=list,
        description="用户手动提炼的技巧卡（每条→一张技巧卡并关联本解法），系统不自动生成",
    )


class ImportResponse(BaseModel):
    problem_id: int
    solution_id: int
    technique_ids: List[int] = []
    is_new_problem: bool = True
    message: str = ""


def _create_user_technique(session, name: str, summary: str) -> TechniqueCard:
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
        code_template="",
        memory_anchors="",
        notes=summary,
        video_demo_link="",
    )
    session.add(technique)
    session.flush()
    return technique


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

        # 2. 建解法卡（代码/语言由系统搬运，思路/复杂度留空待用户补）
        solution = SolutionCard(
            problem_id=problem.id,
            name=f"我的解法（{data.language or '代码'}）",
            language=data.language,
            code=data.code,
            approach=data.description,  # 系统搬运题面/思路描述，用户可改写
            time_complexity="",
            space_complexity="",
            breakthrough="",
            pitfalls="[]",
        )
        session.add(solution)
        session.flush()

        # 3. 由用户手动提炼的技巧卡（每条→一张，关联本解法）
        technique_ids: List[int] = []
        seen_names = set()
        for item in data.techniques:
            name = item.name.strip()
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            technique = _create_user_technique(session, name=name, summary=item.summary.strip())
            session.add(SolutionTechnique(solution_id=solution.id, technique_id=technique.id))
            technique_ids.append(technique.id)

            session.add(ActivityLog(
                type="manual_note",
                card_type="technique",
                card_name=technique.name,
                card_id=technique.id,
                content=f"用户导入时手动提炼技巧卡: {technique.name}",
            ))

        session.commit()
        session.refresh(problem)
        session.refresh(solution)

        msg = "导入成功：新建题目卡与解法卡" if is_new_problem else "已存在该题：追加一条新解法"
        logger.info(f"LeetCode import (slug={data.slug}): problem_id={problem.id}, solution_id={solution.id}, techniques={technique_ids}")

        return ImportResponse(
            problem_id=problem.id,
            solution_id=solution.id,
            technique_ids=technique_ids,
            is_new_problem=is_new_problem,
            message=msg,
        )
    finally:
        session.close()

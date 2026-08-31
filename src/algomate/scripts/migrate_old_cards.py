"""
数据迁移脚本：将旧版 Card 模型数据迁移到三层架构

迁移规则：
- 旧 card_type='tip' → TechniqueCard（保留 Card 复习记录）
- 旧 card_type='problem' → ProblemCard（不创建 Card 记录）
- 旧 CardLink 的 tip_related → solution_techniques 关联
- 由于旧模型没有解法层，tip_related 直接转为 TechniqueCard 关联
"""

import json
import logging
import sys
from datetime import datetime

from algomate.data.database import Database
from algomate.models.cards import Card, _safe_json_parse
from algomate.models.card_links import CardLink
from algomate.models.problem_card import ProblemCard
from algomate.models.solution_card import SolutionCard
from algomate.models.technique_card import TechniqueCard
from algomate.models.solution_technique import SolutionTechnique

logger = logging.getLogger(__name__)


def migrate():
    db = Database.get_instance()
    session = db.get_session()
    migrated = {"tip": 0, "problem": 0, "links": 0}

    try:
        # 1. 迁移 tip 卡牌 → TechniqueCard
        tip_cards = session.query(Card).filter(Card.card_type == "tip").all()
        for card in tip_cards:
            existing = session.query(TechniqueCard).filter(TechniqueCard.card_id == card.id).first()
            if existing:
                continue

            content = _safe_json_parse(card.content, {})
            if not isinstance(content, dict):
                content = {}

            technique = TechniqueCard(
                card_id=card.id,
                name=card.name,
                category="algorithm",
                use_cases=content.get("trigger_condition", ""),
                code_template="",
                memory_anchors="; ".join(content.get("core_ideas", [])),
                proficiency=min(5, max(1, card.review_level + 1)),
                review_interval=1,
            )
            session.add(technique)
            migrated["tip"] += 1

        # 2. 迁移 problem 卡牌 → ProblemCard
        problem_cards = session.query(Card).filter(Card.card_type == "problem").all()
        for card in problem_cards:
            existing = session.query(ProblemCard).filter(ProblemCard.title == card.name).first()
            if existing:
                continue

            content = _safe_json_parse(card.content, {})
            if not isinstance(content, dict):
                content = {}

            problem = ProblemCard(
                title=card.name,
                difficulty={1: "easy", 2: "easy", 3: "medium", 4: "hard", 5: "hard"}.get(card.difficulty, "medium"),
                leetcode_link="",
                tags=json.dumps([card.algorithm_type] if card.algorithm_type else [], ensure_ascii=False),
                my_status="accepted",
            )
            session.add(problem)
            migrated["problem"] += 1

        session.flush()

        # 3. 迁移 CardLink → solution_techniques
        # 旧模型没有解法层，所以需要创建"隐式"解法来连接题目和技巧
        # 如果技巧和题目之间存在关联，我们认为该技巧属于该题目的"默认解法"
        if migrated["problem"] > 0 or migrated["tip"] > 0:
            links = session.query(CardLink).all()
            for link in links:
                source_card = session.query(Card).filter(Card.id == link.source_card_id).first()
                target_card = session.query(Card).filter(Card.id == link.target_card_id).first()
                if not source_card or not target_card:
                    continue

                if source_card.card_type == "tip" and target_card.card_type == "problem":
                    tip_card = source_card
                    prob_card = target_card
                elif target_card.card_type == "tip" and source_card.card_type == "problem":
                    tip_card = target_card
                    prob_card = source_card
                else:
                    continue

                technique = session.query(TechniqueCard).filter(TechniqueCard.card_id == tip_card.id).first()
                problem = session.query(ProblemCard).filter(ProblemCard.title == prob_card.name).first()
                if not technique or not problem:
                    continue

                # 检查是否已有解法连接该题目和技巧
                existing_solution = session.query(SolutionCard).filter(
                    SolutionCard.problem_id == problem.id,
                    SolutionCard.name == f"解法_{technique.name}",
                ).first()

                if not existing_solution:
                    solution = SolutionCard(
                        problem_id=problem.id,
                        name=f"解法_{technique.name}",
                        time_complexity="",
                        space_complexity="",
                        notes="",
                        approach="",
                        code="",
                        pitfalls="[]",
                    )
                    session.add(solution)
                    session.flush()

                    st = SolutionTechnique(
                        solution_id=solution.id,
                        technique_id=technique.id,
                    )
                    session.add(st)
                else:
                    # 检查是否已关联
                    existing_st = session.query(SolutionTechnique).filter(
                        SolutionTechnique.solution_id == existing_solution.id,
                        SolutionTechnique.technique_id == technique.id,
                    ).first()
                    if not existing_st:
                        st = SolutionTechnique(
                            solution_id=existing_solution.id,
                            technique_id=technique.id,
                        )
                        session.add(st)

                migrated["links"] += 1

        session.commit()
        logger.info(
            f"迁移完成: 技巧卡={migrated['tip']}, 题目卡={migrated['problem']}, 关联={migrated['links']}"
        )
        return migrated

    except Exception as e:
        session.rollback()
        logger.error(f"迁移失败: {e}")
        raise
    finally:
        session.close()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger.info("开始数据迁移...")
    result = migrate()
    print(f"\n迁移结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    print("迁移完成！")


if __name__ == "__main__":
    main()
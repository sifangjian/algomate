"""迁移脚本：为已有题目卡补建复习卡(Card)，使题卡成为修炼主单元。

背景：阶段二把修炼主单元从「技巧卡」切换为「题目卡」。历史数据中题目卡
(problem_cards) 未关联复习状态(不创建 Card)。本脚本为所有 card_id 为空的
题目卡补建一张 Card(card_type='problem') 并回填 card_id。

用法：
    uv run python scripts/migrate_problem_review_cards.py
（依赖环境变量 ALGOMATE_DB_PATH 或默认 data/algomate.db）
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from algomate.data.database import Database
from algomate.models.problem_card import ProblemCard
from algomate.models.cards import Card


def main():
    db = Database.get_instance()
    session = db.get_session()
    try:
        problems = session.query(ProblemCard).filter(ProblemCard.card_id.is_(None)).all()
        print(f"找到 {len(problems)} 张无复习卡的题目卡，开始补建...")
        count = 0
        for p in problems:
            tags = []
            try:
                tags = json.loads(p.tags) if p.tags else []
            except (json.JSONDecodeError, TypeError):
                tags = []
            review_card = Card(
                name=p.title,
                card_type="problem",
                algorithm_type=(tags[0] if tags else ""),
                difficulty=3,
                durability=80,
                review_level=0,
                content=json.dumps(
                    {"slug": p.leetcode_slug, "leetcode_link": p.leetcode_link or ""},
                    ensure_ascii=False,
                ),
            )
            session.add(review_card)
            session.flush()
            p.card_id = review_card.id
            count += 1
            print(f"  题卡 #{p.id} '{p.title}' -> 复习卡 #{review_card.id}")
        session.commit()
        print(f"迁移完成，共补建 {count} 张复习卡。")
    finally:
        session.close()


if __name__ == "__main__":
    main()

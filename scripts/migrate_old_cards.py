"""
将旧项目数据库(algomate-old.db)的数据按当前新库结构迁移到当前活跃库(algomate.db)。

设计原则:
- 不改变现有表结构(沿用当前 SQLAlchemy models)。
- 保持所有旧 id 不变(当前活跃库为空, 无冲突), 迁移后重置 sqlite_sequence。
- 字段映射 + 丢弃废弃字段(旧 my_status / algorithm_type / related_solution_ids / category / proficiency / review_interval)。
- 旧 problem_cards 无 leetcode_slug, 从 leetcode_link 解析补全。

用法:
  python scripts/migrate_old_cards.py --dry-run      # 只打印计划, 不写库
  python scripts/migrate_old_cards.py                # 真实迁移(当前活跃库为空时安全)
"""
import argparse
import json
import re
import sqlite3
from datetime import datetime

OLD_DB = "data/algomate-old.db"

from algomate.data.database import Database
from algomate.models.cards import Card
from algomate.models.problem_card import ProblemCard
from algomate.models.solution_card import SolutionCard
from algomate.models.technique_card import TechniqueCard
from algomate.models.solution_technique import SolutionTechnique
from algomate.models.activity_log import ActivityLog


def rq(row, key, default=None):
    """sqlite3.Row 安全取值, 键不存在或值为 None 时返回 default"""
    try:
        v = row[key]
    except IndexError:
        return default
    return v if v is not None else default


def to_dt(v):
    """旧库时间字段可能是字符串或 datetime, 统一转成 datetime(或 None)"""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        s = v.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        # 无法解析则留 None(避免整行失败)
        return None
    return None


def parse_slug(link):
    """从 LeetCode 链接解析 slug: .../problems/<slug>[/description]"""
    if not link:
        return None
    m = re.search(r"/problems/([^/?#]+)", link)
    return m.group(1).strip("/").split("/")[0] if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只打印迁移计划, 不写库")
    args = ap.parse_args()

    old_con = sqlite3.connect(OLD_DB)
    old_con.row_factory = sqlite3.Row
    old_cur = old_con.cursor()

    new_db = Database.get_instance()
    s = new_db.get_session()

    # 防护: 目标库非空则中止, 避免重复迁移污染
    existing = s.query(Card).count() + s.query(ProblemCard).count() + s.query(SolutionCard).count()
    if existing > 0:
        s.close()
        print(f"[中止] 目标活跃库非空(已有 {existing} 行数据), 请先清空再迁移。未写入任何数据。")
        return

    plan = {"cards": 0, "problem_cards": 0, "solution_cards": 0,
            "technique_cards": 0, "solution_techniques": 0, "activity_logs": 0}
    slug_warnings = []

    # 跳过解析失败(无 leetcode_slug)的题卡及其解法和关联技巧
    SKIP_PROBLEM_IDS = [10, 18, 19]
    skip_solution_ids = set()
    skip_technique_ids = set()
    old_cur.execute("SELECT id FROM solution_cards WHERE problem_id IN (?,?,?)", SKIP_PROBLEM_IDS)
    for r in old_cur.fetchall():
        skip_solution_ids.add(r["id"])
    if skip_solution_ids:
        ph = ",".join("?" * len(skip_solution_ids))
        old_cur.execute(f"SELECT DISTINCT technique_id FROM solution_techniques WHERE solution_id IN ({ph})", list(skip_solution_ids))
        for r in old_cur.fetchall():
            skip_technique_ids.add(r["technique_id"])

    # 1) cards (全为 tip 技巧卡复习卡, 沿用 id; 跳过被 skip 的技巧卡)
    old_cur.execute("SELECT * FROM cards")
    for r in old_cur.fetchall():
        if r["id"] in skip_technique_ids:
            continue
        content = rq(r, "content") or "{}"
        try:
            json.loads(content)
        except Exception:
            content = "{}"
        card = Card(
            id=rq(r, "id"), name=rq(r, "name", ""), algorithm_type=rq(r, "algorithm_type") or "",
            difficulty=rq(r, "difficulty") or 3, durability=rq(r, "durability") or 80,
            review_level=rq(r, "review_level") or 0, next_review_date=to_dt(rq(r, "next_review_date")),
            review_count=rq(r, "review_count") or 0, last_reviewed=to_dt(rq(r, "last_reviewed")),
            pending_retake=bool(rq(r, "pending_retake") or 0),
            visual_links=rq(r, "visual_links"), card_type="tip", content=content,
            created_at=to_dt(rq(r, "created_at")) or datetime.now(), updated_at=to_dt(rq(r, "updated_at")) or datetime.now(),
        )
        if not args.dry_run:
            s.add(card)
        plan["cards"] += 1

    # 2) problem_cards (题卡作为修炼主单元需挂接复习卡 Card; 解析 slug; 丢弃 my_status; 跳过 SKIP)
    old_cur.execute("SELECT * FROM problem_cards")
    for r in old_cur.fetchall():
        if r["id"] in SKIP_PROBLEM_IDS:
            continue
        slug = parse_slug(rq(r, "leetcode_link"))
        if not slug:
            slug_warnings.append(f"problem id={r['id']} ({rq(r, 'title')}) 无法解析 slug: {rq(r, 'leetcode_link')}")
        pc = ProblemCard(
            id=rq(r, "id"), title=rq(r, "title", ""), leetcode_slug=slug,
            difficulty=rq(r, "difficulty") or "medium",
            leetcode_link=rq(r, "leetcode_link") or "",
            tags=rq(r, "tags") or "[]", notes=rq(r, "notes") or "",
            is_optimal=0, variants="[]",
            video_demo_link=rq(r, "video_demo_link") or "",
            related_problem_ids=rq(r, "related_problem_ids") or "[]",
            card_id=None,
            created_at=to_dt(rq(r, "created_at")) or datetime.now(), updated_at=to_dt(rq(r, "updated_at")) or datetime.now(),
        )
        if not args.dry_run:
            s.add(pc)
            s.flush()  # 拿 pc.id
            # 题卡挂接复习卡(Card), 导入即到期, 立即可在今日修炼重做(与 import_route 行为一致)
            review_card = Card(
                name=rq(r, "title", ""), card_type="problem",
                algorithm_type=(json.loads(rq(r, "tags") or "[]")[:1] or [""])[0] if rq(r, "tags") else "",
                difficulty=3, durability=80, review_level=0,
                next_review_date=datetime.now(),
                content=json.dumps({"slug": slug, "leetcode_link": rq(r, "leetcode_link") or ""}, ensure_ascii=False),
                created_at=to_dt(rq(r, "created_at")) or datetime.now(), updated_at=datetime.now(),
            )
            s.add(review_card)
            s.flush()
            pc.card_id = review_card.id
            plan["cards"] += 1  # 计入题卡复习卡
        plan["problem_cards"] += 1

    # 3) solution_cards (丢弃 algorithm_type/related_solution_ids; 补 is_optimal=0/language=''; 跳过 SKIP)
    old_cur.execute("SELECT * FROM solution_cards")
    for r in old_cur.fetchall():
        if r["id"] in skip_solution_ids:
            continue
        sc = SolutionCard(
            id=rq(r, "id"), problem_id=rq(r, "problem_id"), name=rq(r, "name", ""),
            language=rq(r, "language") or "", is_optimal=rq(r, "is_optimal") or 0,
            time_complexity=rq(r, "time_complexity") or "", space_complexity=rq(r, "space_complexity") or "",
            breakthrough=rq(r, "breakthrough") or "", approach=rq(r, "approach") or "",
            code=rq(r, "code") or "", pitfalls=rq(r, "pitfalls") or "[]",
            created_at=to_dt(rq(r, "created_at")) or datetime.now(), updated_at=to_dt(rq(r, "updated_at")) or datetime.now(),
        )
        if not args.dry_run:
            s.add(sc)
        plan["solution_cards"] += 1

    # 4) technique_cards (丢弃 category/proficiency/review_interval; card_id 沿用旧 cards.id)
    old_cur.execute("SELECT * FROM technique_cards")
    for r in old_cur.fetchall():
        tc = TechniqueCard(
            id=rq(r, "id"), card_id=rq(r, "card_id"), name=rq(r, "name", ""),
            use_cases=rq(r, "use_cases") or "", code_template=rq(r, "code_template") or "",
            memory_anchors=rq(r, "memory_anchors") or "", notes=rq(r, "notes") or "",
            video_demo_link=rq(r, "video_demo_link") or "",
            created_at=to_dt(rq(r, "created_at")) or datetime.now(), updated_at=to_dt(rq(r, "updated_at")) or datetime.now(),
        )
        if not args.dry_run:
            s.add(tc)
        plan["technique_cards"] += 1

    # 5) solution_techniques (直接搬, 沿用 id; 跳过被 skip 的解法/技巧)
    old_cur.execute("SELECT * FROM solution_techniques")
    for r in old_cur.fetchall():
        if r["id"] in skip_solution_ids or r["technique_id"] in skip_technique_ids:
            continue
        st = SolutionTechnique(id=rq(r, "id"), solution_id=rq(r, "solution_id"), technique_id=rq(r, "technique_id"))
        if not args.dry_run:
            s.add(st)
        plan["solution_techniques"] += 1

    # 6) activity_logs (结构一致, 直接搬, 沿用 id)
    old_cur.execute("SELECT * FROM activity_logs")
    for r in old_cur.fetchall():
        al = ActivityLog(
            id=rq(r, "id"), type=rq(r, "type"), card_type=rq(r, "card_type"),
            card_name=rq(r, "card_name"), card_id=rq(r, "card_id"),
            content=rq(r, "content") or "", details=rq(r, "details"),
            created_at=to_dt(rq(r, "created_at")) or datetime.now(),
        )
        if not args.dry_run:
            s.add(al)
        plan["activity_logs"] += 1

    old_con.close()

    if args.dry_run:
        print("[DRY-RUN] 迁移计划:")
        for k, v in plan.items():
            print(f"  {k}: {v} 行")
        if slug_warnings:
            print(f"\n[警告] {len(slug_warnings)} 个题卡无法解析 leetcode_slug (将留空, 影响 by-slug/导入去重):")
            for w in slug_warnings:
                print("  -", w)
        print("\n(未写入任何数据)")
        return

    s.commit()
    s.close()
    print("[OK] 迁移完成:")
    for k, v in plan.items():
        print(f"  {k}: {v} 行")
    if slug_warnings:
        print(f"\n[注意] {len(slug_warnings)} 个题卡 leetcode_slug 留空(无法从 link 解析), by-slug/去重对该题失效:")
        for w in slug_warnings:
            print("  -", w)


if __name__ == "__main__":
    main()

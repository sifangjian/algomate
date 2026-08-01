"""
卡牌内容迁移脚本：将旧版三层结构（basic_content / practical_content / advanced_content）
迁移到新版 content 字段（tip / problem 结构），并清理旧字段。

用法：docker exec algomate-backend python3 /app/scripts/migrate_cards.py
"""
import json
import sys
import os

# 确保能找到项目模块
sys.path.insert(0, '/app/src')

from algomate.data.database import Database
from algomate.models.cards import Card


def safe_json_parse(value, default=None):
    try:
        return json.loads(value) if value else default
    except (json.JSONDecodeError, TypeError):
        return default


def migrate_card(card):
    """单张卡牌迁移"""
    basic = safe_json_parse(card.basic_content, {}) or {}
    practical = safe_json_parse(card.practical_content, {}) or {}
    advanced = safe_json_parse(card.advanced_content, {}) or {}

    existing_content = safe_json_parse(card.content, {}) or {}
    if existing_content and any(existing_content.get(k) for k in [
        'one_line_definition', 'one_line_problem',
        'trigger_condition', 'core_ideas',
        'solution_approach', 'core_code_snippet',
    ]):
        # 已有新版内容，跳过
        return False

    # 判断卡牌类型
    has_examples = bool(practical.get('examples'))
    has_problem = bool(has_examples or practical.get('applicable_scenarios'))
    has_concept = bool(basic.get('concept_definition'))

    if has_examples and not has_concept:
        # 有例题无概念定义的，归类为题目卡
        card.card_type = 'problem'
        new_content = build_problem_content(basic, practical, advanced)
    else:
        # 默认技巧卡
        card.card_type = 'tip'
        new_content = build_tip_content(basic, practical, advanced)

    card.content = json.dumps(new_content, ensure_ascii=False)
    return True


def build_tip_content(basic, practical, advanced):
    """构建技巧卡内容"""
    concept = (basic.get('concept_definition') or '').strip()
    features = (basic.get('features') or '').strip()
    confusing = (basic.get('confusing_concepts') or '').strip()
    scenarios = (practical.get('applicable_scenarios') or '').strip()
    precautions = (practical.get('precautions') or '').strip()
    mistakes = (advanced.get('common_mistakes') or '').strip()
    extensions = (advanced.get('extensions') or '').strip()
    advanced_sol = (advanced.get('advanced_solutions') or '').strip()

    # 一句话定义
    one_line = concept[:30] if concept else ''

    # 触发条件
    trigger = ''
    if scenarios:
        trigger = f'当看到{scenarios[:20]}，且要求高效求解时，想到对应技巧'

    # 核心思路
    core_ideas = []
    if features:
        core_ideas.append(features[:30])
    if extensions:
        core_ideas.append(extensions[:30])
    if advanced_sol:
        core_ideas.append(advanced_sol[:30])
    if not core_ideas:
        core_ideas = ['待补充']

    # 避坑指南
    pitfalls = []
    if precautions:
        pitfalls.append(f'⚠️ {precautions[:25]}')
    if mistakes:
        pitfalls.append(f'⚠️ {mistakes[:25]}')
    if confusing:
        pitfalls.append(f'⚠️ {confusing[:25]}')

    # 关联题目 - 从旧版例题中提取
    related_problems = []
    examples = practical.get('examples') or []
    for ex in examples[:3]:
        title = (ex.get('title') or '').strip()
        if title:
            related_problems.append(f'[[{title}]]')

    return {
        'one_line_definition': one_line,
        'trigger_condition': trigger,
        'core_ideas': core_ideas,
        'complexity': '',
        'related_problems': related_problems,
        'similar_tips': [],
        'pitfall_guide': pitfalls,
    }


def build_problem_content(basic, practical, advanced):
    """构建题目卡内容"""
    examples = practical.get('examples') or []
    first_example = examples[0] if examples else {}

    title = (first_example.get('title') or '').strip()
    problem_text = (first_example.get('problem') or '').strip()
    solutions = first_example.get('solutions') or []
    first_solution = solutions[0] if solutions else {}

    # 一句话题干
    one_line = problem_text[:40] if problem_text else title[:40]
    # 去掉换行
    one_line = one_line.replace('\n', ' ').replace('\r', '')

    # 解法思路
    approach = []
    principle = (first_solution.get('principle') or '').strip()
    if principle:
        approach.append(principle[:30])
    if not approach:
        approach = ['待补充']

    # 核心代码
    code = (first_solution.get('code') or '').strip()
    code_lines = [l for l in code.split('\n') if l.strip()]
    code_snippet = '\n'.join(code_lines[:5])

    # 复杂度
    complexity = (first_solution.get('complexity') or '').strip()

    return {
        'one_line_problem': one_line,
        'core_skills': [],
        'solution_approach': approach,
        'core_code_snippet': code_snippet,
        'complexity': complexity,
        'related_skills': [],
        'personal_reflection': '',
    }


def main():
    """主函数"""
    db = Database.get_instance()
    session = db.get_session()
    try:
        cards = session.query(Card).all()
        migrated = 0
        skipped = 0
        for card in cards:
            if migrate_card(card):
                migrated += 1
            else:
                skipped += 1
        session.commit()
        print(f'迁移完成：{migrated} 张卡牌已迁移，{skipped} 张卡牌已有新版内容跳过')
    except Exception as e:
        session.rollback()
        print(f'迁移失败: {e}', file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == '__main__':
    main()
"""将旧卡牌扁平字段迁移到三层 JSON 结构"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from algomate.data.database import Database, _ensure_models_imported
from algomate.models.cards import Card
from algomate.config.settings import AppConfig


def migrate_card_tiers():
    config = AppConfig.load()
    db = Database.get_instance(config)
    session = db.get_session()

    try:
        # 检查是否还有旧列（core_concept 列存在说明需要迁移）
        from sqlalchemy import inspect
        engine = db.engine
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('cards')}

        has_old_fields = 'core_concept' in columns
        if not has_old_fields:
            print("旧字段已不存在，无需迁移")
            return

        cards = session.query(Card).all()
        migrated = 0

        for card in cards:
            basic = {}
            practical = {}
            advanced = {}

            # 基础层
            basic['concept_definition'] = _get_str(card, 'core_concept', columns)
            key_points_raw = _get_str(card, 'key_points', columns)
            basic['features'] = _parse_json_list_to_text(key_points_raw)
            basic['confusing_concepts'] = ""

            # 实战层
            examples = []
            code_template = _get_str(card, 'code_template', columns)
            complexity = _get_str(card, 'complexity_analysis', columns)
            if code_template or complexity:
                examples.append({
                    "title": "示例",
                    "problem": _get_str(card, 'typical_problems', columns),
                    "solutions": [{
                        "name": "解法",
                        "code": code_template,
                        "principle": "",
                        "complexity": complexity,
                    }],
                })
            elif 'typical_problems' in columns:
                tp = _get_str(card, 'typical_problems', columns)
                if tp:
                    examples.append({
                        "title": "例题",
                        "problem": tp,
                        "solutions": [],
                    })

            practical['examples'] = examples
            practical['applicable_scenarios'] = _get_str(card, 'use_cases', columns)
            practical['precautions'] = ""

            # 进阶层
            advanced['common_mistakes'] = _get_str(card, 'common_pitfalls', columns)
            advanced['extensions'] = _get_str(card, 'comparison', columns)
            advanced['advanced_solutions'] = _get_str(card, 'common_variants', columns) if 'common_variants' in columns else ""

            card.basic_content = json.dumps(basic, ensure_ascii=False)
            card.practical_content = json.dumps(practical, ensure_ascii=False)
            card.advanced_content = json.dumps(advanced, ensure_ascii=False)
            migrated += 1

        session.commit()
        print(f"迁移完成：{migrated} 张卡牌")

    except Exception as e:
        session.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        session.close()
        db.close()


def _get_str(card, field_name: str, existing_columns: set) -> str:
    if field_name not in existing_columns:
        return ""
    val = getattr(card, field_name, None)
    if val is None:
        return ""
    return str(val).strip()


def _parse_json_list_to_text(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return "\n".join(str(item) for item in parsed)
        return str(parsed)
    except (json.JSONDecodeError, TypeError):
        return value


if __name__ == "__main__":
    migrate_card_tiers()

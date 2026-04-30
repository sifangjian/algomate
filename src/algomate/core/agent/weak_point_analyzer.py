"""
薄弱点分析器模块

提供应战数据的统计分析功能，包括：
- 按算法类型统计胜率
- 识别薄弱秘术
- 生成修习建议
"""

from typing import Dict, List, Any
from collections import defaultdict
from algomate.models import AnswerRecord, Note
from ...data.database import Database
from ...data.repositories import AnswerRecordRepository, NoteRepository


class WeakPointAnalyzer:
    """薄弱点分析器

    通过分析用户的应战记录，识别薄弱秘术并提供修习建议。

    Attributes:
        db: 数据库实例
    """

    def __init__(self, db: Database):
        """初始化分析器

        Args:
            db: 数据库实例
        """
        self.db = db

    def analyze(self, days: int = 30) -> Dict[str, Any]:
        """分析薄弱点

        分析近期的应战记录，识别薄弱秘术。

        Args:
            days: 分析的时间范围（天数），默认30天

        Returns:
            包含以下字段的字典：
            - weak_points: 薄弱点列表
            - overall_accuracy: 总体胜率
            - recommendations: 修习建议列表
        """
        session = self.db.get_session()
        try:
            from datetime import datetime, timedelta

            cutoff_date = datetime.now() - timedelta(days=days)

            records = (
                session.query(AnswerRecord)
                .filter(AnswerRecord.answered_at >= cutoff_date)
                .all()
            )

            type_stats = defaultdict(lambda: {"total": 0, "correct": 0})
            for record in records:
                question = record.question
                if question and question.note:
                    algo_type = question.note.algorithm_type
                    type_stats[algo_type]["total"] += 1
                    if record.is_correct:
                        type_stats[algo_type]["correct"] += 1

            weak_points = []
            for algo_type, stats in type_stats.items():
                if stats["total"] >= 3:
                    accuracy = stats["correct"] / stats["total"]
                    if accuracy < 0.7:
                        weak_points.append({
                            "type": algo_type,
                            "accuracy": accuracy,
                            "total_questions": stats["total"],
                            "correct_questions": stats["correct"],
                        })

            weak_points.sort(key=lambda x: x["accuracy"])

            return {
                "weak_points": weak_points,
                "overall_accuracy": self._calc_overall_accuracy(type_stats),
                "recommendations": self._generate_recommendations(weak_points),
            }
        finally:
            session.close()

    def _calc_overall_accuracy(self, type_stats: Dict) -> float:
        """计算总体胜率

        Args:
            type_stats: 各算法类型的统计数据

        Returns:
            总体胜率
        """
        total = sum(s["total"] for s in type_stats.values())
        correct = sum(s["correct"] for s in type_stats.values())
        return correct / total if total > 0 else 0.0

    def _generate_recommendations(self, weak_points: List[Dict]) -> List[str]:
        """生成修习建议

        根据薄弱点生成针对性的修习建议。

        Args:
            weak_points: 薄弱点列表

        Returns:
            建议列表
        """
        recommendations = []
        for wp in weak_points[:3]:
            recommendations.append(
                f"建议加强{wp['type']}的修习，当前胜率仅{wp['accuracy']:.1%}"
            )
        return recommendations

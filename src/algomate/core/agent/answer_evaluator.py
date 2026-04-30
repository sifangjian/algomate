"""
答案评估器模块

提供用户答案的智能评估功能，包括：
- 调用 AI 评估答案正确性
- 生成详细反馈和改进建议
- 分析用户秘术薄弱点
- 持久化评估结果到数据库
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .chat_client import ChatClient, AnswerEvaluationResult
from algomate.models import Question, AnswerRecord
from ...data.database import Database


class AnswerEvaluator:
    """答案评估器

    负责评估用户答案的正确性，提供详细反馈和改进建议。

    Attributes:
        chat_client: AI 对话客户端实例
        db: 数据库实例（可选）
    """

    def __init__(self, chat_client: ChatClient, db: Optional[Database] = None):
        """初始化评估器

        Args:
            chat_client: AI 对话客户端实例
            db: 数据库实例（可选，用于持久化评估结果）
        """
        self.chat_client = chat_client
        self.db = db

    def evaluate(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        question_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """评估用户答案

        调用 AI 模型评估答案，返回详细的评估结果。

        Args:
            question: 试炼内容
            user_answer: 用户答案
            correct_answer: 参考答案
            question_type: 试炼类型（选择题/简答题/代码题），可选

        Returns:
            包含以下字段的字典：
            - is_correct: 是否正确
            - score: 得分（0-100）
            - feedback: 详细反馈
            - correct_answer: 正确答案
            - explanation: 解析说明
            - improvement: 改进建议
        """
        result = self.chat_client.evaluate_answer(
            question=question,
            user_answer=user_answer,
            correct_answer=correct_answer,
        )

        score = self._calculate_score(result, question_type)

        return {
            "is_correct": result.is_correct,
            "score": score,
            "feedback": result.feedback,
            "correct_answer": correct_answer,
            "explanation": self._generate_explanation(question, correct_answer, question_type),
            "improvement": result.improvement,
        }

    def evaluate_by_question_id(
        self,
        question_id: int,
        user_answer: str,
    ) -> Dict[str, Any]:
        """根据试炼 ID 评估答案

        从数据库加载试炼信息，评估用户答案并保存记录。

        Args:
            question_id: 试炼 ID
            user_answer: 用户答案

        Returns:
            评估结果字典

        Raises:
            ValueError: 当数据库未初始化或试炼不存在时
        """
        if self.db is None:
            raise ValueError("数据库未初始化，无法根据试炼ID评估答案")

        session = self.db.get_session()
        try:
            question = session.query(Question).filter(Question.id == question_id).first()
            if not question:
                raise ValueError(f"试炼 {question_id} 不存在")

            result = self.evaluate(
                question=question.content,
                user_answer=user_answer,
                correct_answer=question.answer,
                question_type=question.question_type,
            )

            answer_record = AnswerRecord(
                question_id=question_id,
                user_answer=user_answer,
                is_correct=result["is_correct"],
                feedback=result["feedback"],
            )
            session.add(answer_record)
            session.commit()

            result["record_id"] = answer_record.id
            return result
        finally:
            session.close()

    def evaluate_and_analyze_weakness(
        self,
        question_id: int,
        user_answer: str,
    ) -> Dict[str, Any]:
        """评估答案并分析薄弱点

        在评估答案的基础上，分析用户的秘术薄弱点。

        Args:
            question_id: 试炼 ID
            user_answer: 用户答案

        Returns:
            包含评估结果和薄弱点分析的字典
        """
        result = self.evaluate_by_question_id(question_id, user_answer)

        if self.db is None:
            return result

        session = self.db.get_session()
        try:
            question = session.query(Question).filter(Question.id == question_id).first()
            if question and question.note:
                weak_points = self._analyze_weak_points(
                    user_answer=user_answer,
                    correct_answer=question.answer,
                    algorithm_type=question.note.algorithm_type,
                )
                result["weak_points"] = weak_points

            return result
        finally:
            session.close()

    def _calculate_score(
        self,
        evaluation: AnswerEvaluationResult,
        question_type: Optional[str] = None,
    ) -> int:
        """计算得分

        根据评估结果和试炼类型计算得分。

        Args:
            evaluation: 评估结果
            question_type: 试炼类型

        Returns:
            得分（0-100）
        """
        if evaluation.is_correct:
            if question_type == "选择题":
                return 100
            elif question_type == "简答题":
                return 90
            elif question_type == "代码题":
                return 95
            else:
                return 100
        else:
            if "部分正确" in evaluation.feedback or "思路正确" in evaluation.feedback:
                return 60
            elif "基本正确" in evaluation.feedback:
                return 75
            else:
                return 30

    def _generate_explanation(
        self,
        question: str,
        correct_answer: str,
        question_type: Optional[str] = None,
    ) -> str:
        """生成解析说明

        根据试炼和正确答案生成解析说明。

        Args:
            question: 试炼内容
            correct_answer: 正确答案
            question_type: 试炼类型

        Returns:
            解析说明文本
        """
        if question_type == "选择题":
            return f"正确答案是：{correct_answer}。请理解为什么这个选项是正确的。"
        elif question_type == "简答题":
            return f"参考答案要点：{correct_answer}"
        elif question_type == "代码题":
            return f"参考实现：\n{correct_answer}"
        else:
            return f"正确答案：{correct_answer}"

    def _analyze_weak_points(
        self,
        user_answer: str,
        correct_answer: str,
        algorithm_type: str,
    ) -> Dict[str, Any]:
        """分析秘术薄弱点

        根据用户答案分析其在特定算法类型上的薄弱点。

        Args:
            user_answer: 用户答案
            correct_answer: 正确答案
            algorithm_type: 算法类型

        Returns:
            薄弱点分析结果
        """
        prompt = f"""分析用户答案，找出其在"{algorithm_type}"方面的秘术薄弱点。

用户答案：{user_answer}
正确答案：{correct_answer}

请返回JSON格式：
{{
    "weak_aspects": ["薄弱方面1", "薄弱方面2"],
    "suggestions": ["改进建议1", "改进建议2"],
    "related_topics": ["相关秘术1", "相关秘术2"]
}}"""

        messages = [{"role": "user", "content": prompt}]
        response = self.chat_client.chat(messages)

        import json
        import re
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "weak_aspects": [],
            "suggestions": [],
            "related_topics": [],
        }

    def batch_evaluate(
        self,
        questions_and_answers: list[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        """批量评估答案

        一次性评估多个答案，适用于批量试炼场景。

        Args:
            questions_and_answers: 包含试炼和答案的字典列表
                每个字典应包含：question_id, question, user_answer, correct_answer

        Returns:
            评估结果列表
        """
        results = []
        for item in questions_and_answers:
            result = self.evaluate(
                question=item.get("question", ""),
                user_answer=item.get("user_answer", ""),
                correct_answer=item.get("correct_answer", ""),
                question_type=item.get("question_type"),
            )
            result["question_id"] = item.get("question_id")
            results.append(result)
        return results

    def get_evaluation_history(
        self,
        question_id: Optional[int] = None,
        limit: int = 10,
    ) -> list[Dict[str, Any]]:
        """获取评估历史

        从数据库查询历史评估记录。

        Args:
            question_id: 试炼 ID（可选，不指定则返回所有）
            limit: 返回记录数量限制

        Returns:
            历史评估记录列表

        Raises:
            ValueError: 当数据库未初始化时
        """
        if self.db is None:
            raise ValueError("数据库未初始化，无法查询评估历史")

        session = self.db.get_session()
        try:
            query = session.query(AnswerRecord)
            if question_id:
                query = query.filter(AnswerRecord.question_id == question_id)

            records = query.order_by(AnswerRecord.answered_at.desc()).limit(limit).all()

            return [
                {
                    "id": record.id,
                    "question_id": record.question_id,
                    "user_answer": record.user_answer,
                    "is_correct": record.is_correct,
                    "feedback": record.feedback,
                    "answered_at": record.answered_at.isoformat() if record.answered_at else None,
                }
                for record in records
            ]
        finally:
            session.close()

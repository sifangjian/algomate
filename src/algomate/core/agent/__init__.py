"""
Agent 模块

提供基于 AI 的算法修习助手功能。

主要组件：
- ChatClient: 通用 LLM API 客户端
- AlgoMateAgent: 基于 Tool-augmented 的智能体
- ToolAugmentedChatClient: 支持 Tool 模式的 ChatClient
- ContentAnalyzer: 内容分析器
- NoteAnalyzer: 心得分析器（已废弃，请使用 ContentAnalyzer）
- QuestionGenerator: 试炼生成器
- AnswerEvaluator: 答案评估器
- WeakPointAnalyzer: 薄弱点分析器
"""

from .chat_client import (
    ChatClient,
    ContentAnalysisResult,
    NoteAnalysisResult,
    Question,
    QuestionsResult,
    AnswerEvaluationResult,
    RouteDecision,
    AgentState,
)
from .base_agent import (
    AlgoMateAgent,
    ToolAugmentedChatClient,
)
from .answer_evaluator import AnswerEvaluator
from .content_analyzer import ContentAnalyzer

__all__ = [
    "ChatClient",
    "ContentAnalysisResult",
    "NoteAnalysisResult",
    "Question",
    "QuestionsResult",
    "AnswerEvaluationResult",
    "RouteDecision",
    "AgentState",
    "AlgoMateAgent",
    "ToolAugmentedChatClient",
    "AnswerEvaluator",
    "ContentAnalyzer",
]
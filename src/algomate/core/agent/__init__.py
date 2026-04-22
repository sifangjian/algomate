"""
Agent 模块

提供基于 AI 的算法学习助手功能。

主要组件：
- ChatClient: 通用 LLM API 客户端
- AlgoMateAgent: 基于 Tool-augmented 的智能体
- ToolAugmentedChatClient: 支持 Tool 模式的 ChatClient
- NoteAnalyzer: 笔记分析器
- QuestionGenerator: 题目生成器
- WeakPointAnalyzer: 薄弱点分析器
"""

from .chat_client import (
    ChatClient,
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

__all__ = [
    "ChatClient",
    "NoteAnalysisResult",
    "Question",
    "QuestionsResult",
    "AnswerEvaluationResult",
    "RouteDecision",
    "AgentState",
    "AlgoMateAgent",
    "ToolAugmentedChatClient",
]
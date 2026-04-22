"""
基础智能体模块

基于 LangChain create_agent v1 实现的 Tool-augmented Agent 架构。

核心设计：
- Tool：LLM 自主调用的能力单元（笔记分析、题目生成、答案评估等）
- Agent：由 create_agent 构建，使用 ReAct 模式自主选择工具

架构图：
    User Input → Agent (LLM + Tools)
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
    Note Tools    Practice     Review
                                 Tools
"""

from __future__ import annotations

import json
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    TypedDict,
    Union,
)
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field
from datetime import datetime, date

from .chat_client import (
    ChatClient,
    NoteAnalysisResult,
    Question,
    QuestionsResult,
    AnswerEvaluationResult,
)


class NoteAnalysisInput(BaseModel):
    """笔记分析输入"""
    note_content: str = Field(description="算法笔记内容（Markdown格式）")


class QuestionGenerationInput(BaseModel):
    """题目生成输入"""
    note_content: str = Field(description="相关笔记内容")
    question_types: Optional[List[str]] = Field(
        default=["选择题", "简答题", "代码题"],
        description="题目类型列表"
    )
    count: int = Field(default=3, description="生成题目数量")


class AnswerEvaluationInput(BaseModel):
    """答案评估输入"""
    question_content: str = Field(description="题目内容")
    user_answer: str = Field(description="用户提交的答案")
    correct_answer: str = Field(description="参考答案")


class NoteSearchInput(BaseModel):
    """笔记搜索输入"""
    query: str = Field(description="搜索关键词或算法类型")
    limit: int = Field(default=5, description="返回结果数量限制")


class ReviewScheduleInput(BaseModel):
    """复习计划输入"""
    days: int = Field(default=7, description="获取未来几天的复习计划")


class AlgoMateAgent:
    """AlgoMate 智能体

    基于 LangChain create_agent 和 Tool 封装的学习助手 Agent。

    核心能力（封装为 Tools）：
    - analyze_note: 分析算法笔记，提取关键知识点
    - generate_questions: 根据笔记或薄弱点生成练习题
    - evaluate_answer: 评估用户答案，给出反馈和改进建议
    - search_notes: 搜索已存储的笔记
    - get_review_schedule: 获取复习计划

    使用方式：
        agent = AlgoMateAgent(chat_client=client, database=db)
        result = agent.invoke({"messages": [HumanMessage(content="帮我分析一下这段笔记")]})
    """

    SYSTEM_PROMPT = """你是 AlgoMate，一个专业的算法学习助手。

你的核心能力：
1. 笔记管理：分析、归类、整理算法笔记
2. 智能出题：根据薄弱点生成针对性练习题
3. 答题评估：分析答案，给出反馈和改进建议
4. 复习引导：基于遗忘曲线安排复习计划

当用户提问时，你应该：
- 理解用户的真实意图（是学习新知识、复习巩固、还是做练习）
- 选择合适的工具来完成任务
- 用清晰友好的语言回复

可用工具：
- analyze_note: 分析算法笔记
- generate_questions: 生成练习题
- evaluate_answer: 评估用户答案
- search_notes: 搜索已存储的笔记
- get_review_schedule: 获取复习计划
"""

    def __init__(
        self,
        chat_client: ChatClient,
        database: Optional[Any] = None,
    ):
        """初始化智能体

        Args:
            chat_client: ChatClient 实例，提供 LLM 和核心方法
            database: 数据库实例（可选，用于笔记存储）
        """
        self.chat_client = chat_client
        self.database = database
        self._tools: Optional[List[BaseTool]] = None
        self._agent: Optional[Any] = None

    @property
    def tools(self) -> List[BaseTool]:
        """获取工具列表"""
        if self._tools is None:
            self._tools = self._create_tools()
        return self._tools

    def _create_tools(self) -> List[BaseTool]:
        """创建工具列表

        将核心能力封装为 LangChain BaseTool。

        Returns:
            工具列表
        """
        return [
            self._create_analyze_note_tool(),
            self._create_generate_questions_tool(),
            self._create_evaluate_answer_tool(),
            self._create_search_notes_tool(),
            self._create_get_review_schedule_tool(),
            self._create_get_weak_points_tool(),
        ]

    def _create_analyze_note_tool(self) -> BaseTool:
        """创建笔记分析工具"""

        @tool(args_schema=NoteAnalysisInput, parse_docstring=True)
        def analyze_note(note_content: str) -> str:
            """分析算法笔记

            当用户分享了一段算法笔记，需要提取关键知识点、判断难度、
            或者理解笔记内容时使用。

            Args:
                note_content: 算法笔记内容（Markdown格式）

            Returns:
                JSON格式的分析结果，包含算法类型、关键知识点、难度等级、标签、总结
            """
            result = self.chat_client.analyze_note(note_content)
            return result.model_dump_json(ensure_ascii=False)

        return analyze_note

    def _create_generate_questions_tool(self) -> BaseTool:
        """创建题目生成工具"""

        @tool(args_schema=QuestionGenerationInput, parse_docstring=True)
        def generate_questions(
            note_content: str,
            question_types: Optional[List[str]] = None,
            count: int = 3,
        ) -> str:
            """生成练习题

            当用户想做练习题、测试自己对某个算法的掌握程度时使用。

            Args:
                note_content: 相关笔记内容
                question_types: 题目类型列表，默认包含选择题、简答题、代码题
                count: 生成题目数量，默认3道

            Returns:
                JSON格式的题目列表
            """
            questions = self.chat_client.generate_questions(
                note_content=note_content,
                question_types=question_types or ["选择题", "简答题", "代码题"],
                count=count,
            )
            return json.dumps(
                [q.model_dump() if hasattr(q, 'model_dump') else q for q in questions],
                ensure_ascii=False,
                indent=2
            )

        return generate_questions

    def _create_evaluate_answer_tool(self) -> BaseTool:
        """创建答案评估工具"""

        @tool(args_schema=AnswerEvaluationInput, parse_docstring=True)
        def evaluate_answer(
            question_content: str,
            user_answer: str,
            correct_answer: str,
        ) -> str:
            """评估用户答案

            当用户提交了答案，需要判断对错、了解改进方向时使用。

            Args:
                question_content: 题目内容
                user_answer: 用户提交的答案
                correct_answer: 参考答案

            Returns:
                JSON格式的评估结果，包含是否正确、详细评价、改进建议
            """
            result = self.chat_client.evaluate_answer(
                question=question_content,
                user_answer=user_answer,
                correct_answer=correct_answer,
            )
            return result.model_dump_json(ensure_ascii=False, indent=2)

        return evaluate_answer

    def _create_search_notes_tool(self) -> BaseTool:
        """创建笔记搜索工具"""

        @tool(args_schema=NoteSearchInput, parse_docstring=True)
        def search_notes(query: str, limit: int = 5) -> str:
            """搜索已存储的笔记

            当用户想查看之前保存的笔记、或者搜索特定算法的笔记时使用。

            Args:
                query: 搜索关键词，可以是算法类型、标签或内容关键词
                limit: 返回结果数量限制，默认5条

            Returns:
                匹配的笔记列表（JSON格式）
            """
            if self.database is None:
                return json.dumps({"error": "数据库未初始化"}, ensure_ascii=False)

            try:
                from ...data.repositories import NoteRepository
                note_repo = NoteRepository(self.database)
                notes = note_repo.search_by_keyword(query, limit=limit)

                result = []
                for note in notes:
                    result.append({
                        "id": note.id,
                        "title": note.title,
                        "algorithm_type": note.algorithm_type,
                        "difficulty": note.difficulty,
                        "summary": note.summary,
                        "tags": json.loads(note.tags) if note.tags else [],
                        "mastery_level": note.mastery_level,
                    })
                return json.dumps(result, ensure_ascii=False, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

        return search_notes

    def _create_get_review_schedule_tool(self) -> BaseTool:
        """创建复习计划工具"""

        @tool(args_schema=ReviewScheduleInput, parse_docstring=True)
        def get_review_schedule(days: int = 7) -> str:
            """获取复习计划

            当用户想了解接下来需要复习哪些内容、
            或者查看复习进度时使用。

            Args:
                days: 获取未来几天的复习计划，默认7天

            Returns:
                复习计划列表（JSON格式），包含笔记信息和建议复习时间
            """
            if self.database is None:
                return json.dumps({"error": "数据库未初始化"}, ensure_ascii=False)

            try:
                from ...data.repositories import NoteRepository
                note_repo = NoteRepository(self.database)
                today = date.today()

                notes_due = note_repo.get_notes_due_for_review(today, days_ahead=days)

                result = []
                for note in notes_due:
                    result.append({
                        "id": note.id,
                        "title": note.title,
                        "algorithm_type": note.algorithm_type,
                        "summary": note.summary,
                        "difficulty": note.difficulty,
                        "mastery_level": note.mastery_level,
                        "review_count": note.review_count,
                    })
                return json.dumps(result, ensure_ascii=False, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

        return get_review_schedule

    def _create_get_weak_points_tool(self) -> BaseTool:
        """创建薄弱点分析工具"""

        @tool
        def get_weak_points(days: int = 30) -> str:
            """分析薄弱点

            当用户想了解自己在哪些算法类型上比较薄弱，
            或者需要针对性练习建议时使用。

            Args:
                days: 分析最近多少天的答题记录，默认30天

            Returns:
                薄弱点分析结果（JSON格式），包含薄弱算法类型、总体正确率、学习建议
            """
            if self.database is None:
                return json.dumps({"error": "数据库未初始化"}, ensure_ascii=False)

            try:
                from ...data.repositories import AnswerRecordRepository
                from ..agent.weak_point_analyzer import WeakPointAnalyzer

                analyzer = WeakPointAnalyzer(self.database)
                result = analyzer.analyze(days=days)
                return json.dumps(result, ensure_ascii=False, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)

        return get_weak_points

    def build_agent(self) -> Any:
        """构建 Tool-augmented Agent

        使用 LangChain create_agent 构建智能体。

        Returns:
            可调用的 Agent，使用 invoke 方法执行
        """
        from langchain.agents import create_agent

        self._agent = create_agent(
            model=self.chat_client.llm,
            tools=self.tools,
            system_prompt=self.SYSTEM_PROMPT,
        )
        return self._agent

    def invoke(
        self,
        input: Union[str, Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """调用智能体

        Args:
            input: 输入，可以是字符串或包含 messages 的字典
            config: 可选的配置参数

        Returns:
            Agent 执行结果
        """
        if self._agent is None:
            self.build_agent()

        if isinstance(input, str):
            input = {"messages": [HumanMessage(content=input)]}

        return self._agent.invoke(input, config=config)

    def chat(self, message: str) -> str:
        """简单对话接口

        Args:
            message: 用户消息

        Returns:
            Agent 回复
        """
        result = self.invoke({"messages": [HumanMessage(content=message)]})
        messages = result.get("messages", [])
        if messages and isinstance(messages[-1], AIMessage):
            return messages[-1].content
        return str(result)


class ToolAugmentedChatClient(ChatClient):
    """Tool-augmented ChatClient

    在原有 ChatClient 基础上增加 Tool-augmented Agent 能力。
    提供向后兼容的接口，同时支持新的 Tool 模式。

    新增功能：
    - tools: 返回可用于 Agent 的工具列表
    - build_agent(): 构建 Tool-augmented Agent

    Example:
        client = ToolAugmentedChatClient(api_key="...")

        # 方式1：使用原有的 chat 方法
        response = client.chat([{"role": "user", "content": "你好"}])

        # 方式2：使用新的 Tool-augmented Agent
        agent = client.build_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": "分析我的笔记"}]})
    """

    def __init__(
        self,
        api_key: str,
        model: str = "glm-4",
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        temperature: float = 0.7,
        timeout: int = 30,
        database: Optional[Any] = None,
    ):
        """初始化客户端

        Args:
            api_key: API 密钥
            model: 模型名称
            base_url: API 基础 URL
            temperature: 生成温度
            timeout: 请求超时时间
            database: 数据库实例（可选）
        """
        super().__init__(api_key, model, base_url, temperature, timeout)
        self.database = database
        self._agent: Optional[AlgoMateAgent] = None

    @property
    def tools(self) -> List[BaseTool]:
        """获取工具列表

        Returns:
            可用于 Agent 的工具列表
        """
        return self.agent.tools

    @property
    def agent(self) -> AlgoMateAgent:
        """获取 Agent 实例

        Returns:
            AlgoMateAgent 实例
        """
        if self._agent is None:
            self._agent = AlgoMateAgent(
                chat_client=self,
                database=self.database,
            )
        return self._agent

    def build_agent(self) -> Any:
        """构建 Tool-augmented Agent

        Returns:
            可调用的 Agent
        """
        return self.agent.build_agent()

    def invoke_agent(
        self,
        input: Union[str, Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """调用 Agent

        Args:
            input: 输入消息或包含 messages 的字典
            config: 可选的配置

        Returns:
            Agent 执行结果
        """
        return self.agent.invoke(input, config=config)
"""
智谱 GLM API 客户端模块

基于 LangChain v1 和 LangGraph 实现的 GLM-4 大模型交互接口，提供：
- 通用对话功能（Chat）
- 笔记分析功能（Note Analysis）
- 题目生成功能（Question Generation）
- 答案评估功能（Answer Evaluation）

LangChain v1 主要更新：
- create_agent: 构建智能体的新标准
- Middleware: 中间件系统，支持动态控制提示、会话摘要等
- content_blocks: 统一的消息内容表示
- 简化的命名空间：langchain.agents, langchain.messages, langchain.tools
"""

from __future__ import annotations

import json
import re
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    TypedDict,
    Union,
)
from pydantic import BaseModel, Field

from langchain.agents import create_agent, AgentMiddleware
from langchain.agents.middleware import AgentMiddleware, ModelRequest
from langchain.agents.middleware.types import ModelResponse
from langchain.agents.structured_output import ToolStrategy
from langchain.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    trim_messages,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END


class NoteAnalysisResult(BaseModel):
    """笔记分析结果结构"""
    algorithm_type: str = Field(description="算法类型（如：动态规划、贪心、DFS等）")
    key_points: List[str] = Field(description="关键知识点列表")
    difficulty: Literal["简单", "中等", "困难"] = Field(description="难度等级")
    tags: List[str] = Field(description="相关标签列表")
    summary: str = Field(description="一句话总结")


class Question(BaseModel):
    """题目结构"""
    question_type: Literal["选择题", "简答题", "代码题"] = Field(description="题目类型")
    content: str = Field(description="题目内容")
    answer: str = Field(description="参考答案")
    explanation: str = Field(description="解析")


class AnswerEvaluationResult(BaseModel):
    """答案评估结果结构"""
    is_correct: bool = Field(description="是否正确")
    feedback: str = Field(description="详细评价")
    improvement: str = Field(description="改进建议")


class QuestionsResult(BaseModel):
    """题目生成结果（包装列表）"""
    questions: List[Question] = Field(description="生成的题目列表")


class GLMState(TypedDict):
    """LangGraph 状态定义

    用于在图节点之间传递状态信息。

    Attributes:
        messages: 对话历史消息列表
        task_type: 当前任务类型（chat/analyze_note/generate_questions/evaluate_answer）
        context: 额外上下文信息
        result: 任务执行结果
        error: 错误信息（如果有）
    """
    messages: Annotated[List[BaseMessage], "对话消息列表"]
    task_type: str
    context: Dict[str, Any]
    result: Optional[Any]
    error: Optional[str]


class ChatClient:
    """智谱 GLM API 客户端

    基于 LangChain v1 create_agent 和 LangGraph 实现的客户端。
    支持通用对话和特定任务（笔记分析、题目生成、答案评估）。

    LangChain v1 新特性使用：
    - create_agent: 简化的智能体构建
    - Middleware: 中间件系统
    - ToolStrategy: 结构化输出
    - content_blocks: 统一消息格式

    Example:
        client = ChatClient(api_key="your-api-key")

        # 通用对话
        response = client.chat([{"role": "user", "content": "你好"}])

        # 笔记分析（结构化输出）
        result = client.analyze_note("# 动态规划\\n\\n动态规划是...")

        # 生成题目
        questions = client.generate_questions(
            note_content="...",
            question_types=["选择题", "代码题"],
            count=3
        )

        # 评估答案
        evaluation = client.evaluate_answer(
            question="什么是动态规划？",
            user_answer="...",
            correct_answer="..."
        )

        # 使用 LangChain v1 create_agent
        agent = client.build_agent(
            system_prompt="你是一个有帮助的算法学习助手。"
        )
        result = agent.invoke({
            "messages": [{"role": "user", "content": "什么是动态规划？"}]
        })
    """

    def __init__(
        self,
        api_key: str,
        model: str = "glm-4",
        temperature: float = 0.7,
        timeout: int = 30,
    ):
        """初始化 GLM 客户端

        Args:
            api_key: 智谱 API 密钥
            model: 模型名称，默认为 glm-4
            temperature: 生成温度参数，控制随机性（0-1）
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"

        self._llm: Optional[ChatOpenAI] = None
        self._agent = None
        self._graph: Optional[StateGraph] = None

    @property
    def llm(self) -> ChatOpenAI:
        """延迟初始化 LLM 实例

        使用延迟初始化可以在创建客户端时不立即建立连接，
        只有在实际调用时才创建 LLM 实例。

        Returns:
            ChatOpenAI 实例
        """
        if self._llm is None:
            self._llm = ChatOpenAI(
                api_key=self.api_key,
                model=self.model,
                temperature=self.temperature,
                timeout=self.timeout,
                base_url=self.base_url,
            )
        return self._llm

    def _get_llm_with_structured_output(
        self,
        output_schema: Optional[type[BaseModel]] = None,
        temperature: Optional[float] = None,
    ) -> ChatOpenAI:
        """获取配置了结构化输出的 LLM

        Args:
            output_schema: Pydantic 模型类，用于结构化输出
            temperature: 可选的温度参数

        Returns:
            配置好的 ChatOpenAI 实例
        """
        temp = temperature if temperature is not None else self.temperature

        llm = ChatOpenAI(
            api_key=self.api_key,
            model=self.model,
            temperature=temp,
            timeout=self.timeout,
            base_url=self.base_url,
        )

        if output_schema:
            llm = llm.with_structured_output(output_schema)

        return llm

    def chat(
        self,
        messages: Union[List[Dict[str, str]], List[BaseMessage]],
        temperature: Optional[float] = None,
    ) -> str:
        """发送对话请求

        基于 LangChain 的通用对话接口。

        Args:
            messages: 对话消息列表
            temperature: 可选的温度参数，覆盖默认值

        Returns:
            模型生成的回复内容

        Raises:
            Exception: 当 API 请求失败时
        """
        messages_list = self._build_messages(messages)

        temp = temperature if temperature is not None else self.temperature
        llm = ChatOpenAI(
            api_key=self.api_key,
            model=self.model,
            temperature=temp,
            timeout=self.timeout,
            base_url=self.base_url,
        )

        response = llm.invoke(messages_list)

        if isinstance(response, AIMessage):
            return response.content
        return str(response)

    def _build_messages(
        self,
        messages: Union[List[Dict[str, str]], List[BaseMessage]],
        system_prompt: Optional[str] = None,
    ) -> List[BaseMessage]:
        """构建 LangChain 格式的消息列表

        将普通字典格式的消息转换为 LangChain 的 BaseMessage 对象，
        便于与 LangChain 生态的其他组件配合使用。

        Args:
            messages: 原始消息列表
            system_prompt: 可选的系统提示词

        Returns:
            LangChain 格式的消息列表
        """
        result: List[BaseMessage] = []

        if system_prompt:
            result.append(SystemMessage(content=system_prompt))

        for msg in messages:
            if isinstance(msg, BaseMessage):
                result.append(msg)
            elif isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "user":
                    result.append(HumanMessage(content=content))
                elif role == "assistant":
                    result.append(AIMessage(content=content))
                elif role == "system":
                    result.append(SystemMessage(content=content))
                else:
                    result.append(HumanMessage(content=content))

        return result

    def analyze_note(
        self,
        note_content: str,
        system_prompt: Optional[str] = None,
    ) -> NoteAnalysisResult:
        """分析算法笔记

        调用大模型分析笔记内容，提取关键信息。
        使用 LangChain v1 结构化输出，直接返回 Pydantic 模型。

        Args:
            note_content: 笔记内容（Markdown格式）
            system_prompt: 可选的系统提示词

        Returns:
            NoteAnalysisResult: 包含分析结果的 Pydantic 模型
        """
        if system_prompt is None:
            system_prompt = """你是一个专业的算法学习助手，擅长分析算法笔记并提取关键信息。
请严格按照JSON格式返回，不要包含任何其他内容。"""

        user_prompt = f"""请分析以下算法笔记，提取关键信息：

{note_content}

请严格按照以下JSON格式返回：
{{
    "algorithm_type": "算法类型（如：动态规划、贪心、DFS等）",
    "key_points": ["关键知识点1", "关键知识点2", "关键知识点3"],
    "difficulty": "难度等级（简单/中等/困难）",
    "tags": ["标签1", "标签2"],
    "summary": "一句话总结"
}}"""

        messages = self._build_messages(
            [{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt
        )

        llm = self._get_llm_with_structured_output(NoteAnalysisResult)
        response = llm.invoke(messages)

        if isinstance(response, NoteAnalysisResult):
            return response
        elif isinstance(response, dict):
            return NoteAnalysisResult(**response)
        else:
            return NoteAnalysisResult(
                algorithm_type="未知",
                key_points=[],
                difficulty="中等",
                tags=[],
                summary=str(response)
            )

    def generate_questions(
        self,
        note_content: str,
        question_types: Optional[List[str]] = None,
        count: int = 3,
        system_prompt: Optional[str] = None,
    ) -> List[Question]:
        """生成练习题

        根据笔记内容生成指定数量和类型的练习题。
        使用 LangChain v1 结构化输出。

        Args:
            note_content: 笔记内容
            question_types: 题目类型列表，默认包含选择题、简答题、代码题
            count: 生成题目数量
            system_prompt: 可选的系统提示词

        Returns:
            List[Question]: 题目列表
        """
        if question_types is None:
            question_types = ["选择题", "简答题", "代码题"]

        if system_prompt is None:
            system_prompt = """你是一个专业的算法出题助手，擅长根据算法笔记生成高质量练习题。
请严格按照JSON格式返回，不要包含任何其他内容。"""

        types_str = "、".join(question_types)
        user_prompt = f"""根据以下算法笔记，生成{count}道练习题：

{note_content}

题目类型要求：{types_str}

请为每道题包含以下JSON字段：
[
    {{
        "question_type": "题目类型",
        "content": "题目内容",
        "answer": "参考答案",
        "explanation": "解析"
    }}
]"""

        messages = self._build_messages(
            [{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt
        )

        llm = self._get_llm_with_structured_output(QuestionsResult)
        response = llm.invoke(messages)

        if isinstance(response, QuestionsResult):
            return response.questions
        elif isinstance(response, dict) and "questions" in response:
            return [Question(**q) for q in response["questions"]]
        elif isinstance(response, list):
            return [Question(**q) if isinstance(q, dict) else q for q in response]
        else:
            return []

    def evaluate_answer(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        system_prompt: Optional[str] = None,
    ) -> AnswerEvaluationResult:
        """评估用户答案

        分析用户答案与参考答案的差异，提供反馈。
        使用 LangChain v1 结构化输出。

        Args:
            question: 题目内容
            user_answer: 用户答案
            correct_answer: 参考答案
            system_prompt: 可选的系统提示词

        Returns:
            AnswerEvaluationResult: 评估结果 Pydantic 模型
        """
        if system_prompt is None:
            system_prompt = """你是一个严格的算法学习评估师，擅长评估用户的答案并给出改进建议。
请严格按照JSON格式返回，不要包含任何其他内容。"""

        user_prompt = f"""题目：{question}
用户答案：{user_answer}
参考答案：{correct_answer}

请分析用户答案，给出以下JSON格式的评估结果：
{{
    "is_correct": true或false,
    "feedback": "详细评价",
    "improvement": "改进建议"
}}"""

        messages = self._build_messages(
            [{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt
        )

        llm = self._get_llm_with_structured_output(AnswerEvaluationResult)
        response = llm.invoke(messages)

        if isinstance(response, AnswerEvaluationResult):
            return response
        elif isinstance(response, dict):
            return AnswerEvaluationResult(**response)
        else:
            return AnswerEvaluationResult(
                is_correct=False,
                feedback=str(response),
                improvement="无法解析评估结果"
            )

    def _parse_json_response(
        self,
        response: str,
        expected_type: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """解析 JSON 响应（备用方法）

        当不使用结构化输出时，可使用此方法从文本中提取 JSON 内容。

        Args:
            response: 模型返回的文本
            expected_type: 期望的解析类型

        Returns:
            解析后的字典或列表对象
        """
        json_match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", response)

        if not json_match:
            return {"raw": response, "error": "无法解析JSON响应"}

        try:
            parsed = json.loads(json_match.group())
            return parsed
        except json.JSONDecodeError as e:
            return {
                "raw": response,
                "error": f"JSON解析失败: {str(e)}"
            }

    def _route_task(self, state: GLMState) -> Literal["chat_node", "analyze_note_node", "generate_questions_node", "evaluate_answer_node"]:
        """根据任务类型路由到不同的处理节点

        作为 LangGraph 的条件分支函数，根据 state 中的 task_type
        决定下一步应该执行哪个节点。

        Args:
            state: 当前图状态

        Returns:
            下一个节点的名称
        """
        task_type = state.get("task_type", "chat")

        task_routes = {
            "chat": "chat_node",
            "analyze_note": "analyze_note_node",
            "generate_questions": "generate_questions_node",
            "evaluate_answer": "evaluate_answer_node",
        }

        return task_routes.get(task_type, "chat_node")

    def _create_chat_node(self, state: GLMState) -> GLMState:
        """对话节点的执行逻辑

        作为 LangGraph 的节点函数处理对话任务。

        Args:
            state: 当前图状态

        Returns:
            更新后的状态
        """
        messages = state.get("messages", [])

        try:
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=self.model,
                temperature=self.temperature,
                timeout=self.timeout,
                base_url=self.base_url,
            )
            response = llm.invoke(messages)

            if isinstance(response, AIMessage):
                new_messages = messages + [response]
            else:
                new_messages = messages + [AIMessage(content=str(response))]

            return {
                **state,
                "messages": new_messages,
                "result": response.content if isinstance(response, AIMessage) else str(response),
                "error": None,
            }
        except Exception as e:
            return {
                **state,
                "error": str(e),
            }

    def _create_analyze_note_node(self, state: GLMState) -> GLMState:
        """笔记分析节点的执行逻辑

        Args:
            state: 当前图状态

        Returns:
            更新后的状态
        """
        context = state.get("context", {})
        note_content = context.get("note_content", "")

        try:
            result = self.analyze_note(note_content)
            return {
                **state,
                "result": result.model_dump() if hasattr(result, 'model_dump') else result,
                "error": None,
            }
        except Exception as e:
            return {
                **state,
                "error": str(e),
            }

    def _create_generate_questions_node(self, state: GLMState) -> GLMState:
        """题目生成节点的执行逻辑

        Args:
            state: 当前图状态

        Returns:
            更新后的状态
        """
        context = state.get("context", {})
        note_content = context.get("note_content", "")
        question_types = context.get("question_types", ["选择题", "简答题", "代码题"])
        count = context.get("count", 3)

        try:
            result = self.generate_questions(
                note_content=note_content,
                question_types=question_types,
                count=count,
            )
            return {
                **state,
                "result": [q.model_dump() if hasattr(q, 'model_dump') else q for q in result],
                "error": None,
            }
        except Exception as e:
            return {
                **state,
                "error": str(e),
            }

    def _create_evaluate_answer_node(self, state: GLMState) -> GLMState:
        """答案评估节点的执行逻辑

        Args:
            state: 当前图状态

        Returns:
            更新后的状态
        """
        context = state.get("context", {})
        question = context.get("question", "")
        user_answer = context.get("user_answer", "")
        correct_answer = context.get("correct_answer", "")

        try:
            result = self.evaluate_answer(
                question=question,
                user_answer=user_answer,
                correct_answer=correct_answer,
            )
            return {
                **state,
                "result": result.model_dump() if hasattr(result, 'model_dump') else result,
                "error": None,
            }
        except Exception as e:
            return {
                **state,
                "error": str(e),
            }

    def build_agent(
        self,
        system_prompt: Optional[str] = None,
        tools: Optional[List] = None,
        middleware: Optional[List[AgentMiddleware]] = None,
    ):
        """使用 LangChain v1 create_agent 构建智能体

        这是 LangChain v1 中构建智能体的标准方式，比 langgraph.prebuilt.create_react_agent
        更简单，同时通过 middleware 提供更高的自定义潜力。

        Args:
            system_prompt: 系统提示词
            tools: 工具列表
            middleware: 中间件列表

        Returns:
            Agent: 可直接调用的智能体

        Example:
            agent = client.build_agent(
                system_prompt="你是一个有帮助的算法学习助手。",
                tools=[search_tool, calculator_tool],
                middleware=[SummarizationMiddleware()]
            )
            result = agent.invoke({
                "messages": [{"role": "user", "content": "什么是动态规划？"}]
            })
        """
        if system_prompt is None:
            system_prompt = "你是一个有帮助的算法学习助手。"

        llm = ChatOpenAI(
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            timeout=self.timeout,
            base_url=self.base_url,
        )

        return create_agent(
            model=llm,
            tools=tools or [],
            system_prompt=system_prompt,
            middleware=middleware or [],
        )

    def build_chat_graph(self) -> StateGraph:
        """构建对话状态图

        使用 LangGraph 构建一个灵活的状态机图结构，支持：
        - chat: 通用对话
        - analyze_note: 笔记分析
        - generate_questions: 题目生成
        - evaluate_answer: 答案评估

        该图结构便于后续扩展和集成到更复杂的 Agent 系统中。

        Returns:
            StateGraph: 编译后的状态图，可直接调用 invoke 方法
        """
        graph = StateGraph(GLMState)

        graph.add_node("chat_node", self._create_chat_node)
        graph.add_node("analyze_note_node", self._create_analyze_note_node)
        graph.add_node("generate_questions_node", self._create_generate_questions_node)
        graph.add_node("evaluate_answer_node", self._create_evaluate_answer_node)

        graph.set_entry_point("_route")
        graph.add_conditional_edges(
            "_route",
            self._route_task,
            {
                "chat_node": "chat_node",
                "analyze_note_node": "analyze_note_node",
                "generate_questions_node": "generate_questions_node",
                "evaluate_answer_node": "evaluate_answer_node",
            }
        )

        for node in ["chat_node", "analyze_note_node", "generate_questions_node", "evaluate_answer_node"]:
            graph.add_edge(node, END)

        self._graph = graph.compile()
        return self._graph

    def invoke_task(
        self,
        task_type: str,
        messages: Optional[List[BaseMessage]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> GLMState:
        """直接调用任务（使用预构建的图）

        提供一个简化的接口来执行各种任务，无需手动构建图。

        Args:
            task_type: 任务类型（chat/analyze_note/generate_questions/evaluate_answer）
            messages: 对话消息列表（用于 chat 任务）
            context: 任务上下文信息

        Returns:
            GLMState: 执行后的最终状态
        """
        if self._graph is None:
            self.build_chat_graph()

        if messages is None:
            messages = []
        if context is None:
            context = {}

        initial_state: GLMState = {
            "messages": messages,
            "task_type": task_type,
            "context": context,
            "result": None,
            "error": None,
        }

        return self._graph.invoke(initial_state)

    def get_graph_diagram(self) -> Any:
        """获取图的图形表示（用于可视化调试）

        Returns:
            图的可视化对象
        """
        if self._graph is None:
            self.build_chat_graph()

        try:
            return self._graph.get_graph().draw_ascii()
        except Exception:
            return "图已构建，请使用 graphviz 可视化"

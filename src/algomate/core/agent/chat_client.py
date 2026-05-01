"""
通用 LLM API 客户端模块

基于 LangChain v1 和 LangGraph 实现的大模型交互接口，提供：
- 通用对话功能（Chat）
- 心得分析功能（Note Analysis）
- 试炼生成功能（Question Generation）
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

# from langchain.agents import create_agent, AgentMiddleware
# from langchain.agents.middleware import AgentMiddleware, ModelRequest
# from langchain.agents.middleware.types import ModelResponse
# from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import (
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
from langgraph.graph import StateGraph, END, START

try:
    from IPython.display import Image, display
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False


class ContentAnalysisResult(BaseModel):
    """内容分析结果结构"""
    algorithm_type: str = Field(description="算法类型（如：动态规划、贪心、DFS等）")
    difficulty: Literal["简单", "中等", "困难"] = Field(description="难度等级")
    tags: List[str] = Field(description="相关标签列表")
    summary: str = Field(description="一句话总结")


NoteAnalysisResult = ContentAnalysisResult


class Question(BaseModel):
    """试炼结构"""
    question_type: Literal["选择题", "简答题", "代码题"] = Field(description="试炼类型")
    content: str = Field(description="试炼内容")
    answer: str = Field(description="参考答案")
    explanation: str = Field(description="解析")


class AnswerEvaluationResult(BaseModel):
    """答案评估结果结构"""
    is_correct: bool = Field(description="是否正确")
    feedback: str = Field(description="详细评价")
    improvement: str = Field(description="改进建议")


class QuestionsResult(BaseModel):
    """试炼生成结果（包装列表）"""
    questions: List[Question] = Field(description="生成的试炼列表")


class RouteDecision(BaseModel):
    """路由决策结构

    Router 节点使用 LLM 判断用户意图后，输出结构化的路由决策。
    """
    next_node: Literal["chat", "practice", "review", "end"] = Field(
        description="下一个执行的节点：chat-聊天, practice-试炼挑战, review-修炼, end-结束对话"
    )
    reason: str = Field(description="决策理由，说明为什么选择该分支")
    context: Dict[str, Any] = Field(default_factory=dict, description="传递给下一个节点的上下文")


class AgentState(TypedDict):
    """循环路由 Agent 状态定义

    用于在图的节点之间传递状态，支持多轮对话和自主路由。

    Attributes:
        messages: 对话历史消息列表（带消息追加 reducer）
        current_node: 当前所在节点名称
        route_decision: 路由决策（由 router 节点设置）
        context: 跨节点传递的上下文信息
        result: 任务执行结果
        should_continue: 是否继续循环
        pending_question: 缓存待回答的试炼（用于 practice 分支）
    """
    messages: Annotated[List[BaseMessage], "对话消息列表"]
    current_node: str
    route_decision: Optional[RouteDecision]
    context: Dict[str, Any]
    result: Optional[Any]
    should_continue: bool
    pending_question: Optional[Dict[str, Any]]


class ChatClient:
    """通用 LLM API 客户端

    基于 LangChain v1 create_agent 和 LangGraph 实现的客户端。
    支持通用对话和特定任务（心得分析、试炼生成、答案评估）。

    LangChain v1 新特性使用：
    - create_agent: 简化的智能体构建
    - Middleware: 中间件系统
    - ToolStrategy: 结构化输出
    - content_blocks: 统一消息格式

    Example:
        client = ChatClient(api_key="your-api-key")

        # 通用对话
        response = client.chat([{"role": "user", "content": "你好"}])

        # 心得分析（结构化输出）
        result = client.analyze_note("# 动态规划\\n\\n动态规划是...")

        # 生成试炼
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
            system_prompt="你是一个有帮助的算法修习助手。"
        )
        result = agent.invoke({
            "messages": [{"role": "user", "content": "什么是动态规划？"}]
        })
    """

    DEFAULT_SYSTEM_PROMPT = """你是 AlgoMate，一个专业的算法修习助手。

## 核心传授原则：渐进式对话

你的回答必须遵循以下原则：

### 1. 精炼聚焦
- 每次回答只聚焦用户问题的一个核心要点，用1-2句话说清楚核心思想
- 配以一个形象易懂的例子帮助理解
- 绝对不要一次性输出过多信息（不要同时讲定义、特征、步骤、代码等）

### 2. 推荐追问
- 每次回答末尾，必须生成2-4个推荐追问话题，引导用户继续探索
- 推荐追问应覆盖不同维度：深入概念、算法步骤、代码示例、应用场景、对比分析等
- 推荐追问应基于当前对话上下文，避免重复已讨论的内容
- 格式要求：在回答正文结束后，用以下格式输出推荐追问：

【推荐追问】
1. 第一个追问
2. 第二个追问
3. 第三个追问

### 3. 回答示例
用户问"什么是二分查找"时，你应该这样回答：

二分查找的核心思想是：在有序集合中，每次将搜索范围缩小一半，从而快速定位目标。

想象你在查字典找"apple"这个单词——你不会从第一页翻到最后一页，而是直接翻到字典中间，发现这一页是"M"开头的，那"apple"一定在前半部分，于是你再把前半部分从中间分开……每次都把范围缩小一半，这就是二分查找！

【推荐追问】
1. 二分查找的时间复杂度是多少？
2. 二分查找的代码怎么写？
3. 什么情况下不能用二分查找？

### 4. 互动引导
- 鼓励用户通过追问逐步深入，而不是一次讲完所有内容
- 根据用户的追问方向灵活调整回答深度
- 如果用户明确要求详细解答，可以适当展开，但仍建议分步进行"""

    def __init__(
        self,
        api_key: str,
        model: str = "glm-4",
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        temperature: float = 0.7,
        timeout: int = 30,
    ):
        """初始化 LLM 客户端

        Args:
            api_key: API 密钥
            model: 模型名称，默认为 glm-4
            base_url: API 基础 URL，默认为智谱 AI 的 URL
            temperature: 生成温度参数，控制随机性（0-1）
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.timeout = timeout

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

        llm = self.llm.bind(temperature=temp)

        if output_schema:
            llm = llm.with_structured_output(output_schema)

        return llm

    def chat(
        self,
        messages: Union[List[Dict[str, str]], List[BaseMessage]],
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """发送对话请求

        基于 LangChain 的通用对话接口。

        Args:
            messages: 对话消息列表
            temperature: 可选的温度参数，覆盖默认值
            system_prompt: 可选的系统提示词，覆盖默认提示

        Returns:
            模型生成的回复内容

        Raises:
            Exception: 当 API 请求失败时
        """
        final_system_prompt = system_prompt if system_prompt is not None else self.DEFAULT_SYSTEM_PROMPT
        messages_list = self._build_messages(messages, system_prompt=final_system_prompt)

        llm = self.llm
        if temperature is not None:
            llm = llm.bind(temperature=temperature)

        response = llm.invoke(messages_list)

        if isinstance(response, AIMessage):
            return response.content
        return str(response)

    def chat_with_suggestions(
        self,
        messages: Union[List[Dict[str, str]], List[BaseMessage]],
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发送对话请求，返回结构化结果（包含推荐追问）

        Args:
            messages: 对话消息列表
            temperature: 可选的温度参数
            system_prompt: 可选的系统提示词

        Returns:
            包含 content 和 suggestions 的字典
        """
        raw_response = self.chat(messages, temperature=temperature, system_prompt=system_prompt)
        clean_content, suggestions = self._parse_suggestions(raw_response)
        return {
            "content": clean_content,
            "suggestions": suggestions,
        }

    def stream_chat(
        self,
        messages: Union[List[Dict[str, str]], List[BaseMessage]],
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ):
        """发送流式对话请求

        基于 LangChain 的流式对话接口，使用 SSE 格式yield每个token。

        Args:
            messages: 对话消息列表
            temperature: 可选的温度参数，覆盖默认值
            system_prompt: 可选的系统提示词，覆盖默认提示

        Yields:
            每个 token 作为一个事件流数据
        """
        final_system_prompt = system_prompt if system_prompt is not None else self.DEFAULT_SYSTEM_PROMPT
        messages_list = self._build_messages(messages, system_prompt=final_system_prompt)

        llm = self.llm
        if temperature is not None:
            llm = llm.bind(temperature=temperature)

        try:
            for chunk in llm.stream(messages_list):
                if isinstance(chunk, str):
                    content = chunk
                elif hasattr(chunk, 'content'):
                    content = chunk.content
                else:
                    content = str(chunk)

                if content:
                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Stream error: {str(e)}'}, ensure_ascii=False)}\n\n"

    def stream_chat_with_suggestions(
        self,
        messages: Union[List[Dict[str, str]], List[BaseMessage]],
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ):
        """发送流式对话请求，流式输出内容，最后输出推荐追问

        先流式输出回答内容，当检测到【推荐追问】标记时，
        将推荐追问作为特殊事件输出。

        Yields:
            SSE格式的事件流数据
        """
        final_system_prompt = system_prompt if system_prompt is not None else self.DEFAULT_SYSTEM_PROMPT
        messages_list = self._build_messages(messages, system_prompt=final_system_prompt)

        llm = self.llm
        if temperature is not None:
            llm = llm.bind(temperature=temperature)

        full_content = ""
        in_suggestions = False

        try:
            for chunk in llm.stream(messages_list):
                if isinstance(chunk, str):
                    content = chunk
                elif hasattr(chunk, 'content'):
                    content = chunk.content
                else:
                    content = str(chunk)

                if content:
                    full_content += content

                    if '【推荐追问】' in content or in_suggestions:
                        in_suggestions = True
                        continue
                    else:
                        yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

            clean_content, suggestions = self._parse_suggestions(full_content)

            if suggestions:
                yield f"data: {json.dumps({'suggestions': suggestions}, ensure_ascii=False)}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Stream error: {str(e)}'}, ensure_ascii=False)}\n\n"

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

    def _parse_suggestions(self, response_text: str) -> tuple[str, list[str]]:
        """解析AI回复，分离回答内容和推荐追问

        Args:
            response_text: AI原始回复文本

        Returns:
            (clean_content, suggestions) 元组
        """
        suggestions = []
        clean_content = response_text

        suggestion_pattern = r'【推荐追问】\s*\n((?:\d+\.\s*.+\n?)+)'
        match = re.search(suggestion_pattern, response_text)

        if match:
            suggestions_block = match.group(1)
            for line in suggestions_block.strip().split('\n'):
                line = line.strip()
                if re.match(r'^\d+\.\s*', line):
                    suggestion = re.sub(r'^\d+\.\s*', '', line).strip()
                    if suggestion:
                        suggestions.append(suggestion)

            clean_content = response_text[:match.start()].rstrip()

        return clean_content, suggestions

    def analyze_note(
        self,
        note_content: str,
        system_prompt: Optional[str] = None,
    ) -> ContentAnalysisResult:
        """分析算法心得

        调用大模型分析心得内容，提取关键信息。
        使用 LangChain v1 结构化输出，直接返回 Pydantic 模型。

        Args:
            note_content: 心得内容（Markdown格式）
            system_prompt: 可选的系统提示词

        Returns:
            ContentAnalysisResult: 包含分析结果的 Pydantic 模型
        """
        if system_prompt is None:
            system_prompt = """你是一个专业的算法修习助手，擅长分析算法心得并提取关键信息。
请严格按照JSON格式返回，不要包含任何其他内容。"""

        user_prompt = f"""请分析以下算法心得，提取关键信息：

{note_content}

请严格按照以下JSON格式返回：
{{
    "algorithm_type": "算法类型（如：动态规划、贪心、DFS等）",
    "difficulty": "难度等级（简单/中等/困难）",
    "tags": ["标签1", "标签2"],
    "summary": "一句话总结"
}}"""

        messages = self._build_messages(
            [{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt
        )

        try:
            llm = self._get_llm_with_structured_output(ContentAnalysisResult)
            response = llm.invoke(messages)

            if isinstance(response, ContentAnalysisResult):
                return response
            elif isinstance(response, dict):
                return ContentAnalysisResult(**response)
            else:
                return ContentAnalysisResult(
                    algorithm_type="未知",
                    difficulty="中等",
                    tags=[],
                    summary=str(response)
                )
        except Exception as e:
            try:
                llm = self.llm
                raw_response = llm.invoke(messages)
                
                if hasattr(raw_response, 'content'):
                    response_text = raw_response.content
                else:
                    response_text = str(raw_response)
                
                response_text = re.sub(r'```json\s*', '', response_text)
                response_text = re.sub(r'```\s*$', '', response_text)
                response_text = response_text.strip()
                
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    json_str = json_match.group()
                    parsed = json.loads(json_str)
                    return ContentAnalysisResult(**parsed)
                
                return ContentAnalysisResult(
                    algorithm_type="未知",
                    difficulty="中等",
                    tags=[],
                    summary=response_text[:100]
                )
            except Exception:
                return ContentAnalysisResult(
                    algorithm_type="未知",
                    difficulty="中等",
                    tags=[],
                    summary="分析失败"
                )

    def generate_questions(
        self,
        note_content: str,
        question_types: Optional[List[str]] = None,
        count: int = 3,
        system_prompt: Optional[str] = None,
    ) -> List[Question]:
        """生成试炼

        根据心得内容生成指定数量和类型的试炼。
        使用 LangChain v1 结构化输出。

        Args:
            note_content: 心得内容
            question_types: 试炼类型列表，默认包含选择题、简答题、代码题
            count: 生成试炼数量
            system_prompt: 可选的系统提示词

        Returns:
            List[Question]: 试炼列表
        """
        if question_types is None:
            question_types = ["选择题", "简答题", "代码题"]

        if system_prompt is None:
            system_prompt = """你是一个专业的算法试炼助手，擅长根据算法心得生成高质量试炼。
请严格按照JSON格式返回，不要包含任何其他内容。"""

        types_str = "、".join(question_types)
        user_prompt = f"""根据以下算法心得，生成{count}道试炼：

{note_content}

试炼类型要求：{types_str}

请严格按照以下JSON格式返回（必须包含 questions 字段）：
{{
    "questions": [
        {{
            "question_type": "试炼类型",
            "content": "试炼内容",
            "answer": "参考答案",
            "explanation": "解析"
        }}
    ]
}}"""

        messages = self._build_messages(
            [{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt
        )

        try:
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
        except Exception as e:
            import json
            import re
            
            try:
                llm = self.llm
                raw_response = llm.invoke(messages)
                
                if hasattr(raw_response, 'content'):
                    response_text = raw_response.content
                else:
                    response_text = str(raw_response)
                
                json_match = re.search(r'\[[\s\S]*\]', response_text)
                if json_match:
                    questions_data = json.loads(json_match.group())
                    return [Question(**q) for q in questions_data if isinstance(q, dict)]
                
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    obj_data = json.loads(json_match.group())
                    if "questions" in obj_data:
                        return [Question(**q) for q in obj_data["questions"] if isinstance(q, dict)]
                
                return []
            except Exception:
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
            question: 试炼内容
            user_answer: 用户答案
            correct_answer: 参考答案
            system_prompt: 可选的系统提示词

        Returns:
            AnswerEvaluationResult: 评估结果 Pydantic 模型
        """
        if system_prompt is None:
            system_prompt = """你是一个严格的算法修习评估师，擅长评估用户的答案并给出改进建议。
请严格按照JSON格式返回，不要包含任何其他内容。"""

        user_prompt = f"""试炼：{question}
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

        try:
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
        except Exception as e:
            try:
                llm = self.llm
                raw_response = llm.invoke(messages)
                
                if hasattr(raw_response, 'content'):
                    response_text = raw_response.content
                else:
                    response_text = str(raw_response)
                
                response_text = re.sub(r'```json\s*', '', response_text)
                response_text = re.sub(r'```\s*$', '', response_text)
                response_text = response_text.strip()
                
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    json_str = json_match.group()
                    parsed = json.loads(json_str)
                    return AnswerEvaluationResult(**parsed)
                
                return AnswerEvaluationResult(
                    is_correct=False,
                    feedback=response_text,
                    improvement="无法解析评估结果"
                )
            except Exception:
                return AnswerEvaluationResult(
                    is_correct=False,
                    feedback="评估失败",
                    improvement="请稍后重试"
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

    def _route_task(self, state: AgentState) -> Literal["chat", "practice", "review", "end"]:
        """根据任务类型路由到不同的处理节点

        作为 LangGraph 的条件分支函数，根据 state 中的 route_decision
        决定下一步应该执行哪个节点。

        Args:
            state: 当前图状态

        Returns:
            下一个节点的名称
        """
        route_decision = state.get("route_decision")
        if route_decision is None:
            print("[ROUTER] route_decision 为空，默认路由到 chat")
            return "chat"

        print(f"[ROUTER] 路由到节点: {route_decision.next_node} | 原因: {route_decision.reason}")
        return route_decision.next_node

    def _create_router_node(self, state: AgentState) -> AgentState:
        """路由节点：LLM 自主判断用户意图

        分析用户的最新消息和对话历史，决定下一步应该执行什么任务。

        Args:
            state: 当前图状态

        Returns:
            更新后的状态，包含 route_decision
        """
        print("[NODE] 进入 router 节点，开始路由决策")
        messages = state.get("messages", [])

        if not messages:
            return {
                **state,
                "route_decision": RouteDecision(
                    next_node="chat",
                    reason="默认进入聊天模式",
                    context={}
                ),
                "should_continue": True,
            }

        system_prompt = """你是一个算法修习助手，负责理解用户意图并决定下一步操作。

用户可能处于以下几种模式：
- chat: 用户想闲聊、讨论算法问题、或者一般对话
- practice: 用户想做试炼、应战测试
- review: 用户想修炼算法秘术、查看功力卡片
- end: 用户想结束对话

根据用户的消息内容，判断用户当前意图。如果不确定，默认进入 chat 模式。

请以 JSON 格式返回你的决策：
{
    "next_node": "chat/practice/review/end",
    "reason": "判断理由",
    "context": {}  // 可选的上下文信息
}"""

        from langchain_core.messages import HumanMessage

        try:
            llm = self._get_llm_with_structured_output(RouteDecision, temperature=0.3)
            router_messages = [SystemMessage(content=system_prompt)] + messages

            response = llm.invoke(router_messages)

            if isinstance(response, RouteDecision):
                return {
                    **state,
                    "route_decision": response,
                    "should_continue": response.next_node != "end",
                }
            else:
                return {
                    **state,
                    "route_decision": RouteDecision(
                        next_node="chat",
                        reason="路由解析失败，进入聊天模式",
                        context={}
                    ),
                    "should_continue": True,
                }
        except Exception as e:
            return {
                **state,
                "route_decision": RouteDecision(
                    next_node="end",
                    reason=f"路由出错: {str(e)}",
                    context={}
                ),
                "should_continue": False,
            }

    def _create_chat_node(self, state: AgentState) -> AgentState:
        """聊天节点：处理一般对话

        Args:
            state: 当前图状态

        Returns:
            更新后的状态
        """
        print("[NODE] 进入 chat 节点")
        messages = state.get("messages", [])

        try:
            chat_messages = self._build_messages(messages, system_prompt=self.DEFAULT_SYSTEM_PROMPT)
            response = self.llm.invoke(chat_messages)

            if isinstance(response, AIMessage):
                new_messages = messages + [response]
            else:
                new_messages = messages + [AIMessage(content=str(response))]

            return {
                **state,
                "messages": new_messages,
                "current_node": "chat",
                "result": response.content if isinstance(response, AIMessage) else str(response),
            }
        except Exception as e:
            return {
                **state,
                "messages": messages + [AIMessage(content=f"抱歉，发生了错误: {str(e)}")],
                "current_node": "chat",
                "result": None,
            }

    def _create_practice_node(self, state: AgentState) -> AgentState:
        """试炼节点：生成试炼让用户应战并评估

        Args:
            state: 当前图状态

        Returns:
            更新后的状态
        """
        context = state.get("context", {})
        messages = state.get("messages", [])
        pending_question = state.get("pending_question")

        try:
            if pending_question is None:
                note_content = context.get("note_content", "算法修习")
                questions = self.generate_questions(
                    note_content=note_content,
                    question_types=["选择题", "简答题"],
                    count=1,
                )
                if not questions:
                    return {
                        **state,
                        "messages": messages + [AIMessage(content="抱歉，无法生成试炼。")],
                        "current_node": "practice",
                        "pending_question": None,
                    }

                q = questions[0]
                pending_q = q.model_dump() if hasattr(q, 'model_dump') else q

                practice_message = f"""好的，让我们来挑战一道试炼：

**试炼类型**：{pending_q.get('question_type', '未知')}

**试炼内容**：
{pending_q.get('content', '')}

请回答这道题，我会评估你的答案。"""

                return {
                    **state,
                    "messages": messages + [AIMessage(content=practice_message)],
                    "current_node": "practice",
                    "pending_question": pending_q,
                    "context": {**context, "current_question": pending_q},
                }
            else:
                user_answer = None
                for msg in reversed(messages):
                    if isinstance(msg, HumanMessage):
                        user_answer = msg.content
                        break

                if user_answer is None:
                    return {
                        **state,
                        "current_node": "practice",
                        "pending_question": pending_question,
                    }

                evaluation = self.evaluate_answer(
                    question=pending_question.get("content", ""),
                    user_answer=user_answer,
                    correct_answer=pending_question.get("answer", ""),
                )

                eval_result = evaluation.model_dump() if hasattr(evaluation, 'model_dump') else evaluation
                feedback = eval_result.get("feedback", "") if isinstance(eval_result, dict) else str(evaluation)
                improvement = eval_result.get("improvement", "") if isinstance(eval_result, dict) else ""

                response_text = f"""**答案评估**：
{feedback}

**改进建议**：
{improvement}

还想继续试炼还是换个话题？"""

                return {
                    **state,
                    "messages": messages + [AIMessage(content=response_text)],
                    "current_node": "practice",
                    "pending_question": None,
                    "result": eval_result,
                }
        except Exception as e:
            return {
                **state,
                "messages": messages + [AIMessage(content=f"试炼过程出错: {str(e)}")],
                "current_node": "practice",
                "pending_question": None,
            }

    def _create_review_node(self, state: AgentState) -> AgentState:
        """修炼节点：帮助用户修炼算法秘术

        Args:
            state: 当前图状态

        Returns:
            更新后的状态
        """
        print("[NODE] 进入 review 节点")
        context = state.get("context", {})
        messages = state.get("messages", [])

        note_content = context.get("note_content", "")
        review_type = context.get("review_type", "general")

        system_prompt = """你是一个算法修炼助手。请根据用户的请求，以友好且交互的方式帮助用户修炼算法秘术。
你可以：
- 解释重要概念
- 提供功力技巧
- 用图解方式说明算法步骤
- 与用户互动确认理解程度

用简洁清晰的语言进行修炼，保持与用户的互动。"""

        try:
            if review_type == "general":
                prompt = f"请帮用户修炼以下算法秘术，用简洁易懂的方式说明关键概念：\n\n{note_content or '算法与数据结构'}"
            else:
                prompt = f"用户请求修炼：{review_type}"

            review_messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]
            response = self.llm.invoke(review_messages)

            response_text = response.content if isinstance(response, AIMessage) else str(response)
            review_text = f"""📚 **修炼时间**

{response_text}

还想修炼其他内容吗，或者想做些试炼？"""

            return {
                **state,
                "messages": messages + [AIMessage(content=review_text)],
                "current_node": "review",
                "result": response_text,
            }
        except Exception as e:
            return {
                **state,
                "messages": messages + [AIMessage(content=f"修炼过程出错: {str(e)}")],
                "current_node": "review",
            }

    def _should_continue(self, state: AgentState) -> bool:
        """判断是否继续循环

        Args:
            state: 当前图状态

        Returns:
            True 如果应该继续，False 如果应该结束
        """
        return state.get("should_continue", True)

    def _create_waiting_node(self, state: AgentState) -> AgentState:
        """等待节点：暂停图执行，等待外部输入新消息

        这个节点是图与外部世界的边界。当图执行到这个节点时，
        应该暂停并将控制权交回给外部调用者。外部调用者获取
        当前状态中的 messages，添加用户的新输入后，
        重新调用 invoke 并传入更新后的 messages。

        外部调用示例：
            state = graph.invoke(initial_state)
            # 获取 AI 的回复
            ai_response = state["messages"][-1]
            # ... 显示给用户，等待用户输入 ...

            # 用户输入后，添加新消息并继续
            state["messages"].append(HumanMessage(content=user_input))
            state["should_continue"] = True
            state = graph.invoke(state)

        Args:
            state: 当前图状态

        Returns:
            更新后的状态，将 should_continue 设为 False 以暂停
        """
        print("[NODE] 进入 waiting 节点，等待外部输入")
        return {
            **state,
            "should_continue": False,
            "current_node": "waiting",
        }

    def build_agent(
        self,
        system_prompt: Optional[str] = None,
        tools: Optional[List] = None,
        middleware: Optional[List[Any]] = None,
    ):
        """使用 LangGraph v1 构建智能体

        当提供 tools 时，内部使用 create_agent 构建支持工具调用的 ReAct 智能体。
        当不提供 tools 时，使用自定义状态图。

        Args:
            system_prompt: 系统提示词
            tools: 工具列表，支持 LangChain 工具
            middleware: 中间件列表（预留接口）

        Returns:
            可直接调用的智能体，使用 invoke 方法执行
        """
        return self.build_chat_graph(
            tools=tools,
            system_prompt=system_prompt,
        )

    def build_chat_graph(
        self,
        tools: Optional[List] = None,
        system_prompt: Optional[str] = None,
    ) -> StateGraph:
        """构建循环路由状态图

        使用 LangGraph v1 API 构建自主路由的对话智能体：

        架构图：
            START → router → chat → router
                      ↓
                    practice → router
                      ↓
                    review → router
                      ↓
                     end

        每轮对话后，Router 节点（LLM）会分析用户意图，
        自主决定下一步执行哪个分支，实现多轮循环对话。

        Args:
            tools: 可选的 LangChain 工具列表，提供时启用 ReAct 模式
            system_prompt: 系统提示词

        Returns:
            StateGraph: 编译后的状态图，可直接调用 invoke 方法
        """
        if tools:
            from langchain.agents import create_agent

            if system_prompt is None:
                system_prompt = "你是一个有帮助的算法修习助手。"

            return create_agent(
                model=self.llm,
                tools=tools,
                system_prompt=system_prompt,
            )

        graph = StateGraph(AgentState)

        graph.add_node("router", self._create_router_node)
        graph.add_node("chat", self._create_chat_node)
        graph.add_node("practice", self._create_practice_node)
        graph.add_node("review", self._create_review_node)

        graph.set_entry_point("router")

        graph.add_conditional_edges(
            "router",
            self._route_task, 
            {
                "chat": "chat",
                "practice": "practice",
                "review": "review",
                "end": END,
            }
        )

        graph.add_conditional_edges(
            "chat",
            lambda state: "waiting" if state.get("should_continue", True) else END,
            {
                "waiting": "waiting",
            }
        )

        graph.add_conditional_edges(
            "practice",
            lambda state: "waiting" if state.get("should_continue", True) else END,
            {
                "waiting": "waiting",
            }
        )

        graph.add_conditional_edges(
            "review",
            lambda state: "waiting" if state.get("should_continue", True) else END,
            {
                "waiting": "waiting",
            }
        )

        graph.add_node("waiting", self._create_waiting_node)

        graph.add_conditional_edges(
            "waiting",
            lambda state: "router" if state.get("should_continue", False) else END,
            {
                "router": "router",
                END: END,
            }
        )

        self._graph = graph.compile()
        return self._graph

    def invoke_task(
        self,
        state: Optional[AgentState] = None,
        messages: Optional[List[BaseMessage]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentState:
        """调用任务（使用预构建的循环图）

        支持两种模式：
        1. 首次调用：不传入 state，传入 messages 和 context
        2. 继续调用：传入从上次调用返回的 state（已包含 messages），
           图会在 waiting 节点暂停，等待外部添加新消息后继续

        外部循环示例：
            # 首次调用
            state = client.invoke_task(
                messages=[HumanMessage(content="你好")]
            )
            print(state["messages"][-1].content)  # AI 回复

            # 用户输入后，继续
            state["messages"].append(HumanMessage(content="我想挑战试炼"))
            state["should_continue"] = True
            state = client.invoke_task(state=state)

        Args:
            state: 已存在的状态（用于继续之前的对话），如果为 None 则创建新状态
            messages: 对话消息列表（仅在 state 为 None 时使用）
            context: 任务上下文信息（仅在 state 为 None 时使用）

        Returns:
            AgentState: 执行后的最终状态
        """
        if self._graph is None:
            self.build_chat_graph()

        if state is not None:
            return self._graph.invoke(state)

        if messages is None:
            messages = []
        if context is None:
            context = {}

        initial_state: AgentState = {
            "messages": messages,
            "current_node": "router",
            "route_decision": None,
            "context": context,
            "result": None,
            "should_continue": True,
            "pending_question": None,
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
            image = self._graph.get_graph().draw_mermaid_png()
            if IPYTHON_AVAILABLE:
                display(Image(image))
                return "图已构建, 请在jupyter notebook查看"
            else:
                return "图已构建, 但IPython不可用，无法在当前环境显示"
        except Exception:
            return "图已构建, 可视化失败"

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/learning", tags=["修习"])
logger = logging.getLogger(__name__)


@router.get("/topics")
async def get_learning_topics():
    topics = {
        "categories": [
            {
                "id": "sorting",
                "name": "排序算法",
                "icon": "📊",
                "topics": ["冒泡排序", "选择排序", "插入排序", "快速排序", "归并排序", "堆排序"]
            },
            {
                "id": "searching",
                "name": "查找算法",
                "icon": "🔍",
                "topics": ["二分查找", "顺序查找", "哈希查找"]
            },
            {
                "id": "dynamic_programming",
                "name": "动态规划",
                "icon": "🎯",
                "topics": ["基础DP", "背包问题", "最长公共子序列", "最短路径"]
            },
            {
                "id": "graph",
                "name": "图论",
                "icon": "🕸️",
                "topics": ["BFS", "DFS", "最短路径", "最小生成树"]
            },
            {
                "id": "tree",
                "name": "树结构",
                "icon": "🌲",
                "topics": ["二叉树遍历", "二叉搜索树", "平衡树", "线段树"]
            },
            {
                "id": "recursion",
                "name": "递归与回溯",
                "icon": "🔄",
                "topics": ["递归", "回溯", "阶乘与斐波那契", "全排列", "组合", "N皇后"]
            }
        ]
    }
    return topics


@router.post("/chat")
async def learning_chat(message: dict):
    from algomate.core.agent.chat_client import ChatClient

    topic = message.get("topic", "")
    question = message.get("question", "")
    conversation_history = message.get("history", [])

    if not question:
        return {"error": "问题不能为空"}

    system_prompt = f"""你是一个专业的算法修习导师，擅长用简洁清晰的方式讲解算法知识。

当前修习主题：{topic}

请用易于理解的方式解释，并穿插适当的例子和图示说明。
如果用户提问，要耐心解答，可以适当提问引导用户思考。
保持对话生动有趣，避免过于学术化。"""

    def generate():
        from algomate.config.settings import AppConfig
        config = AppConfig.load()
        client = ChatClient(api_key=config.LLM_API_KEY)

        try:
            for chunk in client.stream_chat(
                messages=conversation_history + [{"role": "user", "content": question}],
                system_prompt=system_prompt
            ):
                yield chunk
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("learning_chat stream error: %s", e, exc_info=True)
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/generate-quiz")
async def generate_quiz(request: dict):
    from algomate.core.agent.question_generator import QuestionGenerator

    topic = request.get("topic", "")

    if not topic:
        return {"error": "主题不能为空"}

    try:
        generator = QuestionGenerator()
        prompt = f"""针对"{topic}"这个算法主题，生成3道高质量的试炼，包括1道选择题、1道简答题和1道LeetCode挑战。

要求：
- 选择题必须有4个选项（A、B、C、D），只有一个正确答案
- 简答题考查对概念和原理的理解
- LeetCode挑战需要推荐一道LeetCode题目

请返回JSON格式，包含一个questions数组：
{{
    "questions": [
        {{
            "question_type": "选择题",
            "content": "试炼内容（包含选项A、B、C、D）",
            "answer": "正确答案",
            "explanation": "解析"
        }},
        {{
            "question_type": "简答题",
            "content": "试炼内容",
            "answer": "参考答案要点",
            "explanation": "解析"
        }},
        {{
            "question_type": "LeetCode挑战",
            "content": "试炼描述",
            "answer": "解题思路要点",
            "explanation": "解题思路",
            "leetcode_url": "https://leetcode.cn/problems/xxx/",
            "leetcode_title": "LeetCode题目标题",
            "leetcode_difficulty": "Easy/Medium/Hard"
        }}
    ]
}}"""
        messages = [{"role": "user", "content": prompt}]
        result = generator.chat_client.chat(messages)

        import re
        json_match = re.search(r'\[[\s\S]*\]|\{[\s\S]*\}', result)
        if json_match:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict) and "questions" in parsed:
                return {"questions": parsed["questions"], "topic": topic}
            elif isinstance(parsed, list):
                return {"questions": parsed, "topic": topic}
        return {"questions": [], "topic": topic}
    except Exception as e:
        logger.error("generate_topic_questions failed: %s", e, exc_info=True)
        return {"error": str(e)}


@router.post("/save-note")
async def save_learning_note(note_data: dict):
    from algomate.data.database import Database
    from algomate.data.repositories.note_repo import NoteRepository

    db = Database.get_instance()
    note_repo = NoteRepository(db)

    try:
        new_note = note_repo.create(
            title=note_data.get("title") or "",
            content=note_data.get("content") or "",
            algorithm_type=note_data.get("algorithm_type") or "其他",
            difficulty=note_data.get("difficulty") or "中等",
            summary=note_data.get("summary") or "",
            tags=note_data.get("tags") or "[]"
        )
        return {"id": new_note.id, "message": "心得保存成功"}
    except Exception as e:
        logger.error("save_learning_note failed: %s", e, exc_info=True)
        return {"error": str(e)}, 500


@router.get("/explain-concept")
async def explain_concept(topic: str, concept: str):
    from algomate.core.agent.chat_client import ChatClient

    if not concept:
        return {"error": "概念名称不能为空"}

    system_prompt = f"""你是一个专业的算法修习导师，擅长解释算法概念。

当前主题：{topic}
需要解释的概念：{concept}

请用简洁清晰的方式解释这个概念，包括：
1. 什么是这个概念
2. 它的核心思想是什么
3. 常见的应用场景
4. 一个简单的代码示例（如果是代码相关的概念）

请使用 Markdown 格式返回，便于前端渲染。"""

    try:
        from algomate.config.settings import AppConfig
        config = AppConfig.load()
        client = ChatClient(api_key=config.LLM_API_KEY)
        response = client.chat(
            messages=[{"role": "user", "content": f"请解释 {concept} 这个概念"}],
            system_prompt=system_prompt
        )
        return {"explanation": response, "concept": concept, "topic": topic}
    except Exception as e:
        logger.error("explain_concept failed: %s", e, exc_info=True)
        return {"error": str(e)}

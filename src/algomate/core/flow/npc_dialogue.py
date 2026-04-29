"""
NPC对话流程模块

实现与NPC的完整对话流程，包括：
- 开始对话
- 继续对话
- 结束对话并生成卡牌

对话流程：
    1. 用户进入秘境，选择NPC
    2. 获取NPC信息（avatar, greeting, topics）
    3. 用户选择话题或自由提问
    4. 调用 chat_client.chat() 获取NPC回复
    5. 更新对话历史
    6. 用户选择：
       a) 继续提问 → 返回步骤3
       b) 结束学习 → 保存对话记录 → 触发笔记分析 → 生成卡牌
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from algomate.data.database import Database
from algomate.models.npcs import NPC
from algomate.models.dialogue_records import DialogueRecord
from algomate.models.cards import Card, Domain
from algomate.models.notes import Note
from algomate.core.agent.chat_client import ChatClient
from algomate.core.agent.note_analyzer import NoteAnalyzer
from algomate.config.settings import AppConfig


class DialogueState(str, Enum):
    """对话状态枚举"""
    INIT = "init"
    IN_PROGRESS = "in_progress"
    ENDED = "ended"


@dataclass
class DialogueMessage:
    """对话消息数据结构"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DialogueSession:
    """对话会话数据结构"""
    dialogue_id: Optional[int]
    npc_id: int
    npc_name: str
    npc_domain: str
    state: DialogueState
    messages: List[DialogueMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "dialogue_id": self.dialogue_id,
            "npc_id": self.npc_id,
            "npc_name": self.npc_name,
            "npc_domain": self.npc_domain,
            "state": self.state.value,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in self.messages
            ],
            "created_at": self.created_at.isoformat()
        }


class NPCDialogueFlow:
    """NPC对话流程管理器
    
    管理与NPC的完整对话流程，从开始到结束，包括卡牌生成。
    
    使用单例模式，确保整个应用共享同一个实例，避免频繁创建实例导致的
    active_sessions 缓存丢失问题。
    
    Attributes:
        db: 数据库实例
        chat_client: AI对话客户端
        note_analyzer: 笔记分析器
        config: 应用配置
        active_sessions: 活跃的对话会话缓存
        _instance: 单例实例
    """
    _instance: Optional["NPCDialogueFlow"] = None
    
    def __init__(
        self,
        db: Optional[Database] = None,
        chat_client: Optional[ChatClient] = None,
        config: Optional[AppConfig] = None
    ):
        """初始化NPC对话流程管理器
        
        Args:
            db: 数据库实例，默认使用单例
            chat_client: AI对话客户端，默认自动创建
            config: 应用配置，默认自动加载
        """
        self.db = db or Database.get_instance()
        self.config = config or AppConfig.load()
        self.chat_client = chat_client or ChatClient(
            api_key=self.config.LLM_API_KEY,
            model=self.config.LLM_MODEL
        )
        self.note_analyzer = NoteAnalyzer(self.chat_client)
        self.active_sessions: Dict[int, DialogueSession] = {}
    
    @classmethod
    def get_instance(
        cls,
        db: Optional[Database] = None,
        chat_client: Optional[ChatClient] = None,
        config: Optional[AppConfig] = None
    ) -> "NPCDialogueFlow":
        """获取单例实例
        
        Args:
            db: 数据库实例
            chat_client: AI对话客户端
            config: 应用配置
        
        Returns:
            NPCDialogueFlow 单例实例
        """
        if cls._instance is None:
            cls._instance = cls(db, chat_client, config)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例
        
        主要用于测试场景，确保每个测试都有独立的实例。
        """
        cls._instance = None
    
    async def start_dialogue(
        self,
        npc_id: int,
        topic: Optional[str] = None
    ) -> DialogueSession:
        """开始对话，返回初始状态
        
        Args:
            npc_id: NPC ID
            topic: 学习话题（可选）
        
        Returns:
            对话会话对象
        
        Raises:
            ValueError: 当NPC不存在时
        
        Example:
            >>> flow = NPCDialogueFlow()
            >>> session = await flow.start_dialogue(1, "二分查找")
            >>> print(session.npc_name)
            "老夫子"
        """
        session = self.db.get_session()
        try:
            npc = session.query(NPC).filter(NPC.id == npc_id).first()
            if not npc:
                raise ValueError(f"NPC {npc_id} 不存在")
            
            dialogue_session = DialogueSession(
                dialogue_id=None,
                npc_id=npc_id,
                npc_name=npc.name,
                npc_domain=npc.domain,
                state=DialogueState.IN_PROGRESS
            )
            
            greeting = npc.greeting or f"欢迎来到{npc.location}，我是{npc.name}。"
            if topic:
                topics = json.loads(npc.topics) if npc.topics else []
                if topics:
                    greeting += f"\n\n我可以教你以下内容：{', '.join(topics)}"
            
            dialogue_session.messages.append(
                DialogueMessage(
                    role="assistant",
                    content=greeting,
                    timestamp=datetime.now()
                )
            )

            dialogue_content = json.dumps([
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in dialogue_session.messages
            ], ensure_ascii=False)

            dialogue_record = DialogueRecord(
                npc_id=npc_id,
                dialogue_content=dialogue_content,
                generated_cards="[]",
                created_at=datetime.now()
            )
            session.add(dialogue_record)
            session.commit()
            session.refresh(dialogue_record)

            dialogue_session.dialogue_id = dialogue_record.id
            temp_id = id(dialogue_session)
            self.active_sessions[temp_id] = dialogue_session
            self.active_sessions[dialogue_record.id] = dialogue_session

            return dialogue_session
        finally:
            session.close()
    
    async def continue_dialogue(
        self,
        dialogue_id: int,
        user_message: str
    ) -> Dict[str, Any]:
        """继续对话，返回NPC回复
        
        Args:
            dialogue_id: 对话ID（临时ID或数据库ID）
            user_message: 用户消息
        
        Returns:
            包含NPC回复的字典
        
        Raises:
            ValueError: 当对话不存在或已结束时
        
        Example:
            >>> response = await flow.continue_dialogue(1, "什么是二分查找？")
            >>> print(response["npc_response"])
            "二分查找是一种在有序数组中..."
        """
        session = self.db.get_session()
        try:
            dialogue_session = self.active_sessions.get(dialogue_id)
            
            if not dialogue_session:
                db_record = session.query(DialogueRecord).filter(
                    DialogueRecord.id == dialogue_id
                ).first()
                
                if not db_record:
                    raise ValueError(f"对话 {dialogue_id} 不存在")
                
                npc = session.query(NPC).filter(NPC.id == db_record.npc_id).first()
                
                dialogue_session = DialogueSession(
                    dialogue_id=db_record.id,
                    npc_id=db_record.npc_id,
                    npc_name=npc.name,
                    npc_domain=npc.domain,
                    state=DialogueState.IN_PROGRESS
                )
                
                messages_data = json.loads(db_record.dialogue_content)
                for msg in messages_data:
                    dialogue_session.messages.append(
                        DialogueMessage(
                            role=msg["role"],
                            content=msg["content"],
                            timestamp=datetime.fromisoformat(msg["timestamp"]) if isinstance(msg["timestamp"], str) else msg["timestamp"]
                        )
                    )
                
                self.active_sessions[dialogue_id] = dialogue_session
            
            if dialogue_session.state == DialogueState.ENDED:
                raise ValueError("对话已结束，无法继续")
            
            dialogue_session.messages.append(
                DialogueMessage(
                    role="user",
                    content=user_message,
                    timestamp=datetime.now()
                )
            )
            
            npc = session.query(NPC).filter(NPC.id == dialogue_session.npc_id).first()
            
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in dialogue_session.messages
            ]
            
            npc_response = self.chat_client.chat(
                messages=conversation_history,
                system_prompt=npc.system_prompt
            )
            
            dialogue_session.messages.append(
                DialogueMessage(
                    role="assistant",
                    content=npc_response,
                    timestamp=datetime.now()
                )
            )
            
            dialogue_content = json.dumps([
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in dialogue_session.messages
            ], ensure_ascii=False)
            
            db_record = session.query(DialogueRecord).filter(
                DialogueRecord.id == dialogue_id
            ).first()
            if db_record:
                db_record.dialogue_content = dialogue_content
                session.commit()
            
            return {
                "dialogue_id": dialogue_id,
                "npc_response": npc_response,
                "state": dialogue_session.state.value,
                "message_count": len(dialogue_session.messages)
            }
        finally:
            session.close()
    
    async def end_dialogue(
        self,
        dialogue_id: int,
        user_notes: str
    ) -> Dict[str, Any]:
        """结束对话，生成卡牌
        
        Args:
            dialogue_id: 对话ID
            user_notes: 用户笔记内容
        
        Returns:
            包含生成的卡牌列表的字典
        
        Example:
            >>> result = await flow.end_dialogue(1, "二分查找的核心思想是...")
            >>> print(result["cards"])
            [{"name": "二分查找", "domain": "新手森林", ...}]
        """
        session = self.db.get_session()
        try:
            dialogue_session = self.active_sessions.get(dialogue_id)
            
            if not dialogue_session:
                db_record = session.query(DialogueRecord).filter(
                    DialogueRecord.id == dialogue_id
                ).first()
                
                if not db_record:
                    raise ValueError(f"对话 {dialogue_id} 不存在")
                
                npc = session.query(NPC).filter(NPC.id == db_record.npc_id).first()
                
                dialogue_session = DialogueSession(
                    dialogue_id=db_record.id,
                    npc_id=db_record.npc_id,
                    npc_name=npc.name,
                    npc_domain=npc.domain,
                    state=DialogueState.IN_PROGRESS
                )
                
                messages_data = json.loads(db_record.dialogue_content)
                for msg in messages_data:
                    dialogue_session.messages.append(
                        DialogueMessage(
                            role=msg["role"],
                            content=msg["content"],
                            timestamp=datetime.fromisoformat(msg["timestamp"]) if isinstance(msg["timestamp"], str) else msg["timestamp"]
                        )
                    )
                
                self.active_sessions[dialogue_id] = dialogue_session
            
            if dialogue_session.state == DialogueState.ENDED:
                raise ValueError("对话已结束")
            
            dialogue_session.state = DialogueState.ENDED
            
            note = Note(
                title=f"与{dialogue_session.npc_name}的对话笔记",
                content=user_notes,
                npc_id=dialogue_session.npc_id,
                created_at=datetime.now()
            )
            session.add(note)
            session.commit()
            session.refresh(note)
            
            analysis_result = self.note_analyzer.analyze_note(user_notes)
            
            cards = []
            domain = self._map_domain_to_enum(dialogue_session.npc_domain)
            
            card = Card(
                name=analysis_result.algorithm_type or f"{dialogue_session.npc_domain}技巧",
                domain=domain.value if isinstance(domain, Domain) else domain,
                durability=80,
                note_id=note.id,
                created_at=datetime.now()
            )
            session.add(card)
            session.commit()
            session.refresh(card)
            
            cards.append({
                "id": card.id,
                "name": card.name,
                "domain": card.domain,
                "durability": card.durability,
                "note_id": card.note_id
            })
            
            dialogue_content = json.dumps([
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in dialogue_session.messages
            ], ensure_ascii=False)
            
            dialogue_record = DialogueRecord(
                npc_id=dialogue_session.npc_id,
                dialogue_content=dialogue_content,
                generated_cards=json.dumps([card.id for card in session.query(Card).filter(Card.note_id == note.id).all()]),
                created_at=datetime.now()
            )
            session.add(dialogue_record)
            session.commit()
            session.refresh(dialogue_record)
            
            if dialogue_id in self.active_sessions:
                del self.active_sessions[dialogue_id]
            
            return {
                "dialogue_id": dialogue_record.id,
                "note_id": note.id,
                "cards": cards,
                "analysis": {
                    "algorithm_type": analysis_result.algorithm_type,
                    "key_points": analysis_result.key_points,
                    "difficulty": analysis_result.difficulty,
                    "tags": analysis_result.tags,
                    "summary": analysis_result.summary
                }
            }
        finally:
            session.close()
    
    def get_dialogue_history(
        self,
        dialogue_id: int
    ) -> Dict[str, Any]:
        """获取对话历史
        
        Args:
            dialogue_id: 对话ID
        
        Returns:
            对话历史记录
        
        Raises:
            ValueError: 当对话不存在时
        """
        session = self.db.get_session()
        try:
            record = session.query(DialogueRecord).filter(
                DialogueRecord.id == dialogue_id
            ).first()
            
            if not record:
                raise ValueError(f"对话 {dialogue_id} 不存在")
            
            npc = session.query(NPC).filter(NPC.id == record.npc_id).first()
            
            messages = json.loads(record.dialogue_content)
            
            return {
                "dialogue_id": record.id,
                "npc_id": record.npc_id,
                "npc_name": npc.name if npc else "未知NPC",
                "messages": messages,
                "generated_cards": json.loads(record.generated_cards),
                "created_at": record.created_at.isoformat()
            }
        finally:
            session.close()
    
    def _map_domain_to_enum(self, domain_str: str) -> str:
        """将领域字符串映射到枚举值
        
        Args:
            domain_str: 领域字符串
        
        Returns:
            领域枚举值
        """
        domain_mapping = {
            "基础数据结构": Domain.NOVICE_FOREST,
            "树与图": Domain.NOVICE_FOREST,
            "搜索与遍历": Domain.MIST_SWAMP,
            "动态规划": Domain.WISDOM_TEMPLE,
            "贪心算法": Domain.GREED_TOWER,
            "回溯算法": Domain.FATE_MAZE,
            "分治算法": Domain.SPLIT_MOUNTAIN,
            "数学与位运算": Domain.MATH_HALL,
        }
        
        return domain_mapping.get(domain_str, Domain.NOVICE_FOREST).value

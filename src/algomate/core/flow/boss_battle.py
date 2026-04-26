"""
Boss战流程模块

实现完整的Boss挑战流程，包括：
- 为卡牌生成Boss
- 开始战斗
- 提交答案
- 计算掉落奖励

Boss战流程：
    1. 用户选择要使用的卡牌
    2. 系统：
       a) 选择弱点匹配该卡牌的Boss
       b) 或根据卡牌技巧生成新Boss
    3. 显示Boss信息（名称、难度、描述、弱点提示）
    4. 用户进入答题界面
    5. 用户提交答案
    6. 调用 answer_evaluator 评估
    7. 判定结果：
       a) 胜利 → 更新耐久度 → 判定掉宝 → 返回奖励
       b) 失败 → 降低耐久度 → 返回分析
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import random

from algomate.data.database import Database
from algomate.models.bosses import Boss, Difficulty, BossSource
from algomate.models.cards import Card
from algomate.models.questions import Question
from algomate.models.answer_records import AnswerRecord
from algomate.core.agent.chat_client import ChatClient
from algomate.core.agent.question_generator import QuestionGenerator
from algomate.core.agent.answer_evaluator import AnswerEvaluator
from algomate.core.game.durability import DurabilityManager, DurabilityAction
from algomate.core.game.difficulty import DifficultyManager, DifficultyLevel
from algomate.config.settings import AppConfig


class BattleState(str, Enum):
    """战斗状态枚举"""
    PREPARING = "preparing"
    IN_PROGRESS = "in_progress"
    VICTORY = "victory"
    DEFEAT = "defeat"


@dataclass
class BattleSession:
    """战斗会话数据结构"""
    battle_id: Optional[int]
    boss_id: int
    boss_name: str
    boss_difficulty: str
    card_ids: List[int]
    state: BattleState
    question_id: Optional[int] = None
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "battle_id": self.battle_id,
            "boss_id": self.boss_id,
            "boss_name": self.boss_name,
            "boss_difficulty": self.boss_difficulty,
            "card_ids": self.card_ids,
            "state": self.state.value,
            "question_id": self.question_id,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class BattleResult:
    """战斗结果数据结构"""
    is_victory: bool
    durability_change: int
    new_card_dropped: bool
    dropped_card: Optional[Dict[str, Any]] = None
    feedback: str = ""
    improvement: str = ""


class BossBattleFlow:
    """Boss战流程管理器
    
    管理Boss挑战的完整流程，从生成Boss到判定战斗结果。
    
    Attributes:
        db: 数据库实例
        chat_client: AI对话客户端
        question_generator: 题目生成器
        answer_evaluator: 答案评估器
        durability_manager: 耐久度管理器
        difficulty_manager: 难度管理器
        config: 应用配置
        active_battles: 活跃的战斗会话缓存
    """
    
    def __init__(
        self,
        db: Optional[Database] = None,
        chat_client: Optional[ChatClient] = None,
        config: Optional[AppConfig] = None
    ):
        """初始化Boss战流程管理器
        
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
        self.question_generator = QuestionGenerator(self.chat_client)
        self.answer_evaluator = AnswerEvaluator(self.chat_client, self.db)
        self.durability_manager = DurabilityManager()
        self.difficulty_manager = DifficultyManager()
        self.active_battles: Dict[int, BattleSession] = {}
    
    async def generate_boss_for_card(
        self,
        card_id: int,
        difficulty: Optional[str] = None
    ) -> Dict[str, Any]:
        """为指定卡牌生成Boss
        
        Args:
            card_id: 卡牌ID
            difficulty: 难度等级（可选）
        
        Returns:
            生成的Boss信息
        
        Raises:
            ValueError: 当卡牌不存在时
        
        Example:
            >>> boss = await flow.generate_boss_for_card(1, "medium")
            >>> print(boss["name"])
            "迷雾史莱姆王"
        """
        session = self.db.get_session()
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            if not card:
                raise ValueError(f"卡牌 {card_id} 不存在")
            
            existing_boss = session.query(Boss).filter(
                Boss.weakness_domains.contains(card.domain)
            ).first()
            
            if existing_boss:
                return {
                    "id": existing_boss.id,
                    "name": existing_boss.name,
                    "difficulty": existing_boss.difficulty,
                    "weakness_domains": json.loads(existing_boss.weakness_domains),
                    "description": existing_boss.description,
                    "drop_rate": existing_boss.drop_rate,
                    "source": existing_boss.source
                }
            
            boss_difficulty = difficulty or self._determine_difficulty(card.durability)
            
            prompt = f"""根据以下卡牌信息，生成一个Boss挑战：

卡牌信息：
- 名称：{card.name}
- 领域：{card.domain}
- 耐久度：{card.durability}

请生成一个Boss，要求：
1. Boss名称要有创意，符合游戏化风格
2. 难度：{boss_difficulty}
3. 弱点领域包含：{card.domain}
4. 描述要有故事性，游戏化包装
5. 掉宝率根据难度设定（easy=0.8, medium=0.5, hard=0.3）

返回JSON格式：
{{
    "name": "Boss名称",
    "difficulty": "{boss_difficulty}",
    "weakness_domains": ["{card.domain}"],
    "description": "Boss描述",
    "drop_rate": 0.5
}}"""
            
            result = self.chat_client.chat([{"role": "user", "content": prompt}])
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', result)
            if not json_match:
                boss_data = {
                    "name": f"{card.domain}守护者",
                    "difficulty": boss_difficulty,
                    "weakness_domains": [card.domain],
                    "description": f"这是{card.domain}领域的守护Boss，需要使用{card.name}技巧才能击败它。",
                    "drop_rate": 0.5 if boss_difficulty == "medium" else (0.8 if boss_difficulty == "easy" else 0.3)
                }
            else:
                boss_data = json.loads(json_match.group())
            
            new_boss = Boss(
                name=boss_data.get("name", f"{card.domain}守护者"),
                difficulty=boss_data.get("difficulty", boss_difficulty),
                weakness_domains=json.dumps(boss_data.get("weakness_domains", [card.domain]), ensure_ascii=False),
                description=boss_data.get("description", ""),
                source="ai_generated",
                drop_rate=boss_data.get("drop_rate", 0.5)
            )
            session.add(new_boss)
            session.commit()
            session.refresh(new_boss)
            
            return {
                "id": new_boss.id,
                "name": new_boss.name,
                "difficulty": new_boss.difficulty,
                "weakness_domains": json.loads(new_boss.weakness_domains),
                "description": new_boss.description,
                "drop_rate": new_boss.drop_rate,
                "source": new_boss.source
            }
        finally:
            session.close()
    
    async def start_battle(
        self,
        boss_id: int,
        card_ids: List[int]
    ) -> BattleSession:
        """开始战斗，返回战斗状态
        
        Args:
            boss_id: Boss ID
            card_ids: 使用的卡牌ID列表
        
        Returns:
            战斗会话对象
        
        Raises:
            ValueError: 当Boss或卡牌不存在时
        
        Example:
            >>> battle = await flow.start_battle(1, [1, 2])
            >>> print(battle.boss_name)
            "迷雾史莱姆王"
        """
        session = self.db.get_session()
        try:
            boss = session.query(Boss).filter(Boss.id == boss_id).first()
            if not boss:
                raise ValueError(f"Boss {boss_id} 不存在")
            
            cards = session.query(Card).filter(Card.id.in_(card_ids)).all()
            if not cards:
                raise ValueError("未找到有效的卡牌")
            
            for card in cards:
                if card.is_sealed:
                    raise ValueError(f"卡牌 {card.id} 已封印，无法使用")
            
            question_data = self.question_generator.generate_for_note(
                note_content=boss.description,
                count=1
            )
            
            if question_data:
                question = Question(
                    question_type=question_data[0].get("question_type", "简答题"),
                    content=question_data[0].get("content", boss.description),
                    answer=question_data[0].get("answer", ""),
                    explanation=question_data[0].get("explanation", ""),
                    difficulty=boss.difficulty
                )
                session.add(question)
                session.commit()
                session.refresh(question)
                question_id = question.id
            else:
                question_id = None
            
            battle_session = BattleSession(
                battle_id=None,
                boss_id=boss_id,
                boss_name=boss.name,
                boss_difficulty=boss.difficulty,
                card_ids=card_ids,
                state=BattleState.IN_PROGRESS,
                question_id=question_id
            )
            
            temp_id = id(battle_session)
            self.active_battles[temp_id] = battle_session
            
            return battle_session
        finally:
            session.close()
    
    async def submit_answer(
        self,
        battle_id: int,
        user_answer: str
    ) -> BattleResult:
        """提交答案，返回战斗结果
        
        Args:
            battle_id: 战斗ID
            user_answer: 用户答案
        
        Returns:
            战斗结果对象
        
        Raises:
            ValueError: 当战斗不存在或已结束时
        
        Example:
            >>> result = await flow.submit_answer(1, "使用二分查找...")
            >>> print(result.is_victory)
            True
        """
        session = self.db.get_session()
        try:
            battle_session = self.active_battles.get(battle_id)
            
            if not battle_session:
                raise ValueError(f"战斗 {battle_id} 不存在")
            
            if battle_session.state in [BattleState.VICTORY, BattleState.DEFEAT]:
                raise ValueError("战斗已结束")
            
            battle_session.attempts += 1
            
            boss = session.query(Boss).filter(Boss.id == battle_session.boss_id).first()
            
            if battle_session.question_id:
                question = session.query(Question).filter(
                    Question.id == battle_session.question_id
                ).first()
                
                evaluation = self.answer_evaluator.evaluate(
                    question=question.content,
                    user_answer=user_answer,
                    correct_answer=question.answer,
                    question_type=question.question_type
                )
                
                is_correct = evaluation.get("is_correct", False)
            else:
                evaluation = self.answer_evaluator.evaluate(
                    question=boss.description,
                    user_answer=user_answer,
                    correct_answer="正确答案",
                    question_type="简答题"
                )
                is_correct = evaluation.get("is_correct", False)
            
            if is_correct:
                battle_session.state = BattleState.VICTORY
                durability_action = DurabilityAction.BOSS_DEFEAT
            else:
                if battle_session.attempts >= battle_session.max_attempts:
                    battle_session.state = BattleState.DEFEAT
                    durability_action = DurabilityAction.BOSS_FAIL
                else:
                    durability_action = DurabilityAction.BOSS_FAIL
            
            durability_changes = []
            for card_id in battle_session.card_ids:
                card = session.query(Card).filter(Card.id == card_id).first()
                if card:
                    new_durability, is_critical, is_sealed = self.durability_manager.update_durability(
                        current_durability=card.durability,
                        action=durability_action,
                        difficulty=self.difficulty_manager.current_difficulty.value
                    )
                    
                    card.durability = new_durability
                    card.is_sealed = is_sealed
                    card.last_reviewed = datetime.now()
                    
                    durability_changes.append({
                        "card_id": card_id,
                        "old_durability": card.durability,
                        "new_durability": new_durability,
                        "change": new_durability - card.durability
                    })
            
            session.commit()
            
            dropped_card = None
            new_card_dropped = False
            
            if battle_session.state == BattleState.VICTORY:
                dropped_card, new_card_dropped = self._calculate_drops(boss, session)
            
            answer_record = AnswerRecord(
                boss_id=battle_session.boss_id,
                card_id=battle_session.card_ids[0] if battle_session.card_ids else None,
                user_answer=user_answer,
                is_correct=is_correct,
                feedback=evaluation.get("feedback", ""),
                answered_at=datetime.now()
            )
            session.add(answer_record)
            session.commit()
            
            if battle_id in self.active_battles:
                del self.active_battles[battle_id]
            
            return BattleResult(
                is_victory=battle_session.state == BattleState.VICTORY,
                durability_change=sum(dc["change"] for dc in durability_changes),
                new_card_dropped=new_card_dropped,
                dropped_card=dropped_card,
                feedback=evaluation.get("feedback", ""),
                improvement=evaluation.get("improvement", "")
            )
        finally:
            session.close()
    
    def calculate_drops(
        self,
        boss: Boss,
        is_victory: bool
    ) -> Optional[Dict[str, Any]]:
        """计算是否掉落新卡牌
        
        Args:
            boss: Boss对象
            is_victory: 是否胜利
        
        Returns:
            掉落的卡牌信息（如果掉落），否则返回None
        
        Example:
            >>> card = flow.calculate_drops(boss, True)
            >>> if card:
            ...     print(f"获得新卡牌：{card['name']}")
        """
        session = self.db.get_session()
        try:
            dropped_card, new_card_dropped = self._calculate_drops(boss, session)
            return dropped_card
        finally:
            session.close()
    
    def _calculate_drops(
        self,
        boss: Boss,
        session
    ) -> tuple[Optional[Dict[str, Any]], bool]:
        """内部方法：计算掉落
        
        Args:
            boss: Boss对象
            session: 数据库会话
        
        Returns:
            (掉落的卡牌信息, 是否掉落)
        """
        drop_rate = boss.drop_rate
        drop_rate += self.difficulty_manager.get_boss_drop_rate_bonus()
        
        if random.random() < drop_rate:
            weakness_domains = json.loads(boss.weakness_domains)
            
            if weakness_domains:
                domain = random.choice(weakness_domains)
                
                card = Card(
                    name=f"{domain}技巧卡",
                    domain=domain,
                    durability=80,
                    created_at=datetime.now()
                )
                session.add(card)
                session.commit()
                session.refresh(card)
                
                return {
                    "id": card.id,
                    "name": card.name,
                    "domain": card.domain,
                    "durability": card.durability
                }, True
        
        return None, False
    
    def _determine_difficulty(self, durability: int) -> str:
        """根据耐久度确定难度
        
        Args:
            durability: 卡牌耐久度
        
        Returns:
            难度等级
        """
        if durability >= 80:
            return "easy"
        elif durability >= 50:
            return "medium"
        else:
            return "hard"
    
    def get_battle_result(
        self,
        battle_id: int
    ) -> Dict[str, Any]:
        """获取战斗结果
        
        Args:
            battle_id: 战斗ID
        
        Returns:
            战斗结果详情
        
        Raises:
            ValueError: 当战斗不存在时
        """
        session = self.db.get_session()
        try:
            answer_record = session.query(AnswerRecord).filter(
                AnswerRecord.id == battle_id
            ).first()
            
            if not answer_record:
                raise ValueError(f"战斗记录 {battle_id} 不存在")
            
            boss = session.query(Boss).filter(Boss.id == answer_record.boss_id).first()
            
            return {
                "battle_id": battle_id,
                "boss_id": answer_record.boss_id,
                "boss_name": boss.name if boss else "未知Boss",
                "card_id": answer_record.card_id,
                "is_correct": answer_record.is_correct,
                "feedback": answer_record.feedback,
                "answered_at": answer_record.answered_at.isoformat()
            }
        finally:
            session.close()

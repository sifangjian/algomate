"""
业务流程层测试

测试 M5 业务流程层的所有模块：
- M5.1 NPC对话流程
- M5.2 Boss战流程
- M5.3 修炼调度器
- M5.4 邮件提醒系统
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import json

from algomate.core.flow.npc_dialogue import (
    NPCDialogueFlow,
    DialogueState,
    DialogueSession,
    DialogueMessage
)
from algomate.core.flow.boss_battle import (
    BossBattleFlow,
    BattleState,
    BattleSession,
    BattleResult
)
from algomate.core.scheduler.review_scheduler import (
    ReviewScheduler,
    ReviewTask,
    TaskType
)
from algomate.core.scheduler.email_sender import EmailSender


class TestNPCDialogueFlow:
    """NPC对话流程测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        db = Mock()
        session = Mock()
        db.get_session.return_value = session
        return db
    
    @pytest.fixture
    def mock_chat_client(self):
        """模拟聊天客户端"""
        client = Mock()
        client.chat.return_value = "这是NPC的回复"
        client.analyze_note.return_value = Mock(
            algorithm_type="二分查找",
            key_points=["有序数组", "分治思想"],
            difficulty="中等",
            tags=["搜索", "数组"],
            summary="二分查找是一种高效的搜索算法"
        )
        return client
    
    @pytest.fixture
    def dialogue_flow(self, mock_db, mock_chat_client):
        """创建对话流程实例"""
        NPCDialogueFlow.reset_instance()
        return NPCDialogueFlow(
            db=mock_db,
            chat_client=mock_chat_client
        )
    
    def test_dialogue_session_creation(self):
        """测试对话会话创建"""
        session = DialogueSession(
            dialogue_id=1,
            npc_id=1,
            npc_name="老夫子",
            npc_domain="基础数据结构",
            state=DialogueState.IN_PROGRESS
        )
        
        assert session.dialogue_id == 1
        assert session.npc_name == "老夫子"
        assert session.state == DialogueState.IN_PROGRESS
    
    def test_dialogue_message_creation(self):
        """测试对话消息创建"""
        message = DialogueMessage(
            role="user",
            content="什么是二分查找？"
        )
        
        assert message.role == "user"
        assert message.content == "什么是二分查找？"
        assert isinstance(message.timestamp, datetime)
    
    def test_dialogue_session_to_dict(self):
        """测试对话会话转换为字典"""
        session = DialogueSession(
            dialogue_id=1,
            npc_id=1,
            npc_name="老夫子",
            npc_domain="基础数据结构",
            state=DialogueState.IN_PROGRESS
        )
        
        session_dict = session.to_dict()
        
        assert "dialogue_id" in session_dict
        assert "npc_name" in session_dict
        assert "state" in session_dict
        assert session_dict["state"] == "in_progress"


class TestBossBattleFlow:
    """Boss战流程测试"""
    
    def test_battle_session_creation(self):
        """测试战斗会话创建"""
        session = BattleSession(
            battle_id=1,
            boss_id=1,
            boss_name="迷雾史莱姆王",
            boss_difficulty="medium",
            card_ids=[1, 2],
            state=BattleState.IN_PROGRESS
        )
        
        assert session.battle_id == 1
        assert session.boss_name == "迷雾史莱姆王"
        assert session.state == BattleState.IN_PROGRESS
        assert session.card_ids == [1, 2]
    
    def test_battle_result_creation(self):
        """测试战斗结果创建"""
        result = BattleResult(
            is_victory=True,
            durability_change=20,
            new_card_dropped=True,
            dropped_card={"id": 1, "name": "新卡牌"},
            feedback="表现出色！",
            improvement="继续保持"
        )
        
        assert result.is_victory == True
        assert result.durability_change == 20
        assert result.new_card_dropped == True
    
    def test_battle_session_to_dict(self):
        """测试战斗会话转换为字典"""
        session = BattleSession(
            battle_id=1,
            boss_id=1,
            boss_name="迷雾史莱姆王",
            boss_difficulty="medium",
            card_ids=[1],
            state=BattleState.VICTORY
        )
        
        session_dict = session.to_dict()
        
        assert "battle_id" in session_dict
        assert "boss_name" in session_dict
        assert "state" in session_dict
        assert session_dict["state"] == "victory"


class TestReviewScheduler:
    """修炼调度器测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        db = Mock()
        session = Mock()
        db.get_session.return_value = session
        return db
    
    @pytest.fixture
    def scheduler(self, mock_db):
        """创建修炼调度器实例"""
        return ReviewScheduler(db=mock_db)
    
    def test_review_task_creation(self):
        """测试修炼任务创建"""
        task = ReviewTask(
            task_id="review_1",
            task_type=TaskType.CRITICAL_REVIEW,
            card_id=1,
            card_name="二分查找",
            card_domain="新手森林",
            card_durability=25,
            priority="critical",
            reason="濒危卡牌",
            due_date=datetime.now().date()
        )
        
        assert task.task_id == "review_1"
        assert task.task_type == TaskType.CRITICAL_REVIEW
        assert task.card_name == "二分查找"
        assert task.priority == "critical"
    
    def test_review_task_to_dict(self):
        """测试修炼任务转换为字典"""
        task = ReviewTask(
            task_id="review_1",
            task_type=TaskType.FORGETTING_CURVE_REVIEW,
            card_id=1,
            card_name="滑动窗口",
            card_domain="迷雾沼泽",
            card_durability=80,
            priority="high",
            reason="遗忘曲线修炼",
            due_date=datetime.now().date()
        )
        
        task_dict = task.to_dict()
        
        assert "task_id" in task_dict
        assert "task_type" in task_dict
        assert "card_name" in task_dict
        assert task_dict["task_type"] == "forgetting_curve_review"


class TestEmailSender:
    """邮件提醒系统测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock()
        config.SMTP_HOST = "smtp.example.com"
        config.SMTP_PORT = 465
        config.SMTP_USER = "user@example.com"
        config.SMTP_PASSWORD = "password"
        config.EMAIL_FROM = "sender@example.com"
        config.EMAIL_TO = "recipient@example.com"
        config.APP_URL = "http://localhost:3000"
        return config
    
    @pytest.fixture
    def mock_review_scheduler(self):
        """模拟修炼调度器"""
        scheduler = Mock()
        scheduler.generate_daily_tasks.return_value = [
            ReviewTask(
                task_id="review_1",
                task_type=TaskType.CRITICAL_REVIEW,
                card_id=1,
                card_name="二分查找",
                card_domain="新手森林",
                card_durability=25,
                priority="critical",
                reason="濒危卡牌",
                due_date=datetime.now().date()
            )
        ]
        return scheduler
    
    @pytest.fixture
    def email_sender(self, mock_config, mock_review_scheduler):
        """创建邮件发送器实例"""
        return EmailSender(
            config=mock_config,
            review_scheduler=mock_review_scheduler
        )
    
    def test_preview_email_content(self, email_sender):
        """测试预览邮件内容"""
        content = email_sender.preview_email_content()
        
        assert "subject" in content
        assert "body" in content
        assert "算法大陆" in content["subject"]
        assert "冒险者" in content["body"]
    
    def test_build_email_content(self, email_sender):
        """测试构建邮件内容"""
        tasks = [
            ReviewTask(
                task_id="review_1",
                task_type=TaskType.CRITICAL_REVIEW,
                card_id=1,
                card_name="二分查找",
                card_domain="新手森林",
                card_durability=25,
                priority="critical",
                reason="濒危卡牌",
                due_date=datetime.now().date()
            ),
            ReviewTask(
                task_id="review_2",
                task_type=TaskType.FORGETTING_CURVE_REVIEW,
                card_id=2,
                card_name="滑动窗口",
                card_domain="迷雾沼泽",
                card_durability=80,
                priority="high",
                reason="遗忘曲线修炼",
                due_date=datetime.now().date()
            )
        ]
        
        content = email_sender._build_email_content(tasks)
        
        assert "今日任务（2项）" in content["body"]
        assert "濒危卡牌" in content["body"]
        assert "遗忘修炼" in content["body"]
    
    def test_validate_email_config(self, email_sender):
        """测试验证邮件配置"""
        is_valid = email_sender._validate_email_config()
        
        assert is_valid == True
    
    def test_get_recipients(self, email_sender):
        """测试获取收件人列表"""
        recipients = email_sender._get_recipients()
        
        assert isinstance(recipients, list)
        assert len(recipients) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

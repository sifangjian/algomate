"""
业务流程层验证脚本

验证 M5 业务流程层的所有模块是否正确导入和实例化
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """测试所有模块是否可以正确导入"""
    print("=" * 60)
    print("测试模块导入...")
    print("=" * 60)
    
    try:
        print("[OK] 导入 NPC对话流程模块...")
        from algomate.core.flow.npc_dialogue import (
            NPCDialogueFlow,
            DialogueState,
            DialogueSession,
            DialogueMessage
        )
        print("  - NPCDialogueFlow")
        print("  - DialogueState")
        print("  - DialogueSession")
        print("  - DialogueMessage")
    except Exception as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    try:
        print("\n[OK] 导入 Boss战流程模块...")
        from algomate.core.flow.boss_battle import (
            BossBattleFlow,
            BattleState,
            BattleSession,
            BattleResult
        )
        print("  - BossBattleFlow")
        print("  - BattleState")
        print("  - BattleSession")
        print("  - BattleResult")
    except Exception as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    try:
        print("\n[OK] 导入 复习调度器模块...")
        from algomate.core.scheduler.review_scheduler import (
            ReviewScheduler,
            ReviewTask,
            TaskType
        )
        print("  - ReviewScheduler")
        print("  - ReviewTask")
        print("  - TaskType")
    except Exception as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    try:
        print("\n[OK] 导入 邮件提醒系统模块...")
        from algomate.core.scheduler.email_sender import EmailSender
        print("  - EmailSender")
    except Exception as e:
        print(f"[FAIL] 导入失败: {e}")
        return False
    
    return True


def test_data_structures():
    """测试数据结构是否可以正确创建"""
    print("\n" + "=" * 60)
    print("测试数据结构创建...")
    print("=" * 60)
    
    from datetime import datetime
    from algomate.core.flow.npc_dialogue import DialogueSession, DialogueMessage, DialogueState
    from algomate.core.flow.boss_battle import BattleSession, BattleResult, BattleState
    from algomate.core.scheduler.review_scheduler import ReviewTask, TaskType
    
    try:
        print("\n[OK] 创建 DialogueSession...")
        session = DialogueSession(
            dialogue_id=1,
            npc_id=1,
            npc_name="老夫子",
            npc_domain="基础数据结构",
            state=DialogueState.IN_PROGRESS
        )
        print(f"  - dialogue_id: {session.dialogue_id}")
        print(f"  - npc_name: {session.npc_name}")
        print(f"  - state: {session.state.value}")
    except Exception as e:
        print(f"[FAIL] 创建失败: {e}")
        return False
    
    try:
        print("\n[OK] 创建 DialogueMessage...")
        message = DialogueMessage(
            role="user",
            content="什么是二分查找？"
        )
        print(f"  - role: {message.role}")
        print(f"  - content: {message.content}")
    except Exception as e:
        print(f"[FAIL] 创建失败: {e}")
        return False
    
    try:
        print("\n[OK] 创建 BattleSession...")
        battle = BattleSession(
            battle_id=1,
            boss_id=1,
            boss_name="迷雾史莱姆王",
            boss_difficulty="medium",
            card_ids=[1, 2],
            state=BattleState.IN_PROGRESS
        )
        print(f"  - battle_id: {battle.battle_id}")
        print(f"  - boss_name: {battle.boss_name}")
        print(f"  - state: {battle.state.value}")
    except Exception as e:
        print(f"[FAIL] 创建失败: {e}")
        return False
    
    try:
        print("\n[OK] 创建 BattleResult...")
        result = BattleResult(
            is_victory=True,
            durability_change=20,
            new_card_dropped=True,
            feedback="表现出色！"
        )
        print(f"  - is_victory: {result.is_victory}")
        print(f"  - durability_change: {result.durability_change}")
    except Exception as e:
        print(f"[FAIL] 创建失败: {e}")
        return False
    
    try:
        print("\n[OK] 创建 ReviewTask...")
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
        print(f"  - task_id: {task.task_id}")
        print(f"  - task_type: {task.task_type.value}")
        print(f"  - card_name: {task.card_name}")
    except Exception as e:
        print(f"[FAIL] 创建失败: {e}")
        return False
    
    return True


def test_to_dict_methods():
    """测试 to_dict 方法"""
    print("\n" + "=" * 60)
    print("测试 to_dict 方法...")
    print("=" * 60)
    
    from datetime import datetime
    from algomate.core.flow.npc_dialogue import DialogueSession, DialogueState
    from algomate.core.flow.boss_battle import BattleSession, BattleState
    from algomate.core.scheduler.review_scheduler import ReviewTask, TaskType
    
    try:
        print("\n[OK] 测试 DialogueSession.to_dict()...")
        session = DialogueSession(
            dialogue_id=1,
            npc_id=1,
            npc_name="老夫子",
            npc_domain="基础数据结构",
            state=DialogueState.IN_PROGRESS
        )
        session_dict = session.to_dict()
        print(f"  - 包含字段: {list(session_dict.keys())}")
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False
    
    try:
        print("\n[OK] 测试 BattleSession.to_dict()...")
        battle = BattleSession(
            battle_id=1,
            boss_id=1,
            boss_name="迷雾史莱姆王",
            boss_difficulty="medium",
            card_ids=[1],
            state=BattleState.VICTORY
        )
        battle_dict = battle.to_dict()
        print(f"  - 包含字段: {list(battle_dict.keys())}")
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False
    
    try:
        print("\n[OK] 测试 ReviewTask.to_dict()...")
        task = ReviewTask(
            task_id="review_1",
            task_type=TaskType.FORGETTING_CURVE_REVIEW,
            card_id=1,
            card_name="滑动窗口",
            card_domain="迷雾沼泽",
            card_durability=80,
            priority="high",
            reason="遗忘曲线复习",
            due_date=datetime.now().date()
        )
        task_dict = task.to_dict()
        print(f"  - 包含字段: {list(task_dict.keys())}")
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False
    
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("M5 业务流程层验证")
    print("=" * 60)
    
    results = []
    
    results.append(("模块导入", test_imports()))
    results.append(("数据结构创建", test_data_structures()))
    results.append(("to_dict方法", test_to_dict_methods()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 所有测试通过！")
    else:
        print("[ERROR] 部分测试失败")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

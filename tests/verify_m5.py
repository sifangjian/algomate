"""
业务流程层代码验证脚本

验证 M5 业务流程层的代码文件是否存在和语法是否正确
"""

import ast
import os
import sys


def test_file_existence():
    """测试文件是否存在"""
    print("=" * 60)
    print("测试文件存在性...")
    print("=" * 60)
    
    base_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'algomate')
    
    files_to_check = [
        ('core/flow/__init__.py', '流程模块初始化'),
        ('core/flow/npc_dialogue.py', 'NPC对话流程'),
        ('core/flow/boss_battle.py', 'Boss战流程'),
        ('core/scheduler/__init__.py', '调度器模块初始化'),
        ('core/scheduler/review_scheduler.py', '复习调度器'),
        ('core/scheduler/email_sender.py', '邮件提醒系统'),
        ('models/__init__.py', '模型模块初始化'),
        ('models/review_records.py', '复习记录模型'),
        ('models/learning_progress.py', '学习进度模型'),
    ]
    
    all_exist = True
    for file_path, description in files_to_check:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"[OK] {description}: {file_path} ({size} bytes)")
        else:
            print(f"[FAIL] {description}: {file_path} 不存在")
            all_exist = False
    
    return all_exist


def test_syntax():
    """测试Python语法是否正确"""
    print("\n" + "=" * 60)
    print("测试Python语法...")
    print("=" * 60)
    
    base_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'algomate')
    
    files_to_check = [
        'core/flow/__init__.py',
        'core/flow/npc_dialogue.py',
        'core/flow/boss_battle.py',
        'core/scheduler/__init__.py',
        'core/scheduler/review_scheduler.py',
        'core/scheduler/email_sender.py',
        'models/__init__.py',
        'models/review_records.py',
        'models/learning_progress.py',
    ]
    
    all_valid = True
    for file_path in files_to_check:
        full_path = os.path.join(base_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
            ast.parse(code)
            print(f"[OK] {file_path} 语法正确")
        except SyntaxError as e:
            print(f"[FAIL] {file_path} 语法错误: {e}")
            all_valid = False
        except FileNotFoundError:
            print(f"[SKIP] {file_path} 文件不存在")
    
    return all_valid


def test_code_structure():
    """测试代码结构"""
    print("\n" + "=" * 60)
    print("测试代码结构...")
    print("=" * 60)
    
    base_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'algomate')
    
    checks = []
    
    file_path = os.path.join(base_path, 'core/flow/npc_dialogue.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_items = [
        'class DialogueState',
        'class DialogueMessage',
        'class DialogueSession',
        'class NPCDialogueFlow',
        'async def start_dialogue',
        'async def continue_dialogue',
        'async def end_dialogue',
    ]
    
    for item in required_items:
        if item in content:
            print(f"[OK] npc_dialogue.py 包含: {item}")
            checks.append(True)
        else:
            print(f"[FAIL] npc_dialogue.py 缺少: {item}")
            checks.append(False)
    
    file_path = os.path.join(base_path, 'core/flow/boss_battle.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_items = [
        'class BattleState',
        'class BattleSession',
        'class BattleResult',
        'class BossBattleFlow',
        'async def generate_boss_for_card',
        'async def start_battle',
        'async def submit_answer',
    ]
    
    for item in required_items:
        if item in content:
            print(f"[OK] boss_battle.py 包含: {item}")
            checks.append(True)
        else:
            print(f"[FAIL] boss_battle.py 缺少: {item}")
            checks.append(False)
    
    file_path = os.path.join(base_path, 'core/scheduler/review_scheduler.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_items = [
        'class TaskType',
        'class ReviewTask',
        'class ReviewScheduler',
        'def generate_daily_tasks',
        'def get_upcoming_reviews',
        'def get_review_statistics',
    ]
    
    for item in required_items:
        if item in content:
            print(f"[OK] review_scheduler.py 包含: {item}")
            checks.append(True)
        else:
            print(f"[FAIL] review_scheduler.py 缺少: {item}")
            checks.append(False)
    
    file_path = os.path.join(base_path, 'core/scheduler/email_sender.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_items = [
        'class EmailSender',
        'def send_review_reminder',
        'def test_email_config',
        'def preview_email_content',
        'def _build_email_content',
    ]
    
    for item in required_items:
        if item in content:
            print(f"[OK] email_sender.py 包含: {item}")
            checks.append(True)
        else:
            print(f"[FAIL] email_sender.py 缺少: {item}")
            checks.append(False)
    
    file_path = os.path.join(base_path, 'models/review_records.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_items = [
        'class ReviewRecord',
        'class ReviewRecordCreate',
        'class ReviewRecordResponse',
    ]
    
    for item in required_items:
        if item in content:
            print(f"[OK] review_records.py 包含: {item}")
            checks.append(True)
        else:
            print(f"[FAIL] review_records.py 缺少: {item}")
            checks.append(False)
    
    file_path = os.path.join(base_path, 'models/learning_progress.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_items = [
        'class LearningProgress',
        'class LearningProgressCreate',
        'class LearningProgressResponse',
    ]
    
    for item in required_items:
        if item in content:
            print(f"[OK] learning_progress.py 包含: {item}")
            checks.append(True)
        else:
            print(f"[FAIL] learning_progress.py 缺少: {item}")
            checks.append(False)
    
    return all(checks)


def test_models_init():
    """测试模型模块导出"""
    print("\n" + "=" * 60)
    print("测试模型模块导出...")
    print("=" * 60)
    
    base_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'algomate')
    
    file_path = os.path.join(base_path, 'models/__init__.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_exports = [
        'ReviewRecord',
        'ReviewRecordCreate',
        'ReviewRecordResponse',
        'LearningProgress',
        'LearningProgressCreate',
        'LearningProgressResponse',
    ]
    
    all_exported = True
    for export in required_exports:
        if f'"{export}"' in content or f"'{export}'" in content:
            print(f"[OK] models/__init__.py 导出: {export}")
        else:
            print(f"[FAIL] models/__init__.py 未导出: {export}")
            all_exported = False
    
    return all_exported


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("M5 业务流程层代码验证")
    print("=" * 60)
    
    results = []
    
    results.append(("文件存在性", test_file_existence()))
    results.append(("Python语法", test_syntax()))
    results.append(("代码结构", test_code_structure()))
    results.append(("模型导出", test_models_init()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 所有代码验证通过！")
        print("\nM5 业务流程层已成功实现，包含以下模块：")
        print("  1. NPC对话流程 (npc_dialogue.py)")
        print("  2. Boss战流程 (boss_battle.py)")
        print("  3. 复习调度器 (review_scheduler.py)")
        print("  4. 邮件提醒系统 (email_sender.py)")
        print("\n模型已统一迁移到 models/ 目录：")
        print("  - ReviewRecord (review_records.py)")
        print("  - LearningProgress (learning_progress.py)")
    else:
        print("[ERROR] 部分代码验证失败")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

"""
API路由测试脚本

测试所有注册的API端点是否正常工作
"""

import sys
import os

sys.path.insert(0, "f:\\workspace\\python\\algomate\\src")
os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi.testclient import TestClient
from algomate.main import AlgomateApp


def test_api_registration():
    """测试API是否正确注册"""
    print("=" * 60)
    print("测试 API 路由注册")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    routes = [route.path for route in app.api_app.routes]

    print("\n已注册的路由:")
    for route in sorted(routes):
        print(f"   {route}")

    expected_prefixes = [
        "/api/notes",
        "/api/cards",
        "/api/bosses",
        "/api/npcs",
        "/api/questions",
        "/api/dialogues",
        "/api/review-records",
        "/api/learning-progress",
        "/api/practice",
        "/api/progress",
        "/api/settings",
        "/api/dashboard",
        "/api/learning",
        "/api/boss",
        "/api/battle",
        "/api/tasks",
        "/api/dialogue",
        "/api/user",
    ]

    print("\n检查必需的路由前缀:")
    missing_routes = []
    for prefix in expected_prefixes:
        found = any(route.startswith(prefix) for route in routes)
        status = "[OK]" if found else "[MISSING]"
        print(f"   {status} {prefix}")
        if not found:
            missing_routes.append(prefix)

    if missing_routes:
        print(f"\n[ERROR] 缺少以下路由: {missing_routes}")
        return False

    print("\n[OK] 所有必需的路由都已注册")
    return True


def test_notes_api():
    """测试笔记API"""
    print("\n" + "=" * 60)
    print("测试 /api/notes 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/notes")
    print(f"   GET /api/notes -> {response.status_code}")

    response = client.get("/api/notes/1")
    print(f"   GET /api/notes/1 -> {response.status_code}")

    return response.status_code == 200


def test_cards_api():
    """测试卡牌API"""
    print("\n" + "=" * 60)
    print("测试 /api/cards 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/cards")
    print(f"   GET /api/cards -> {response.status_code}")

    response = client.get("/api/cards/critical")
    print(f"   GET /api/cards/critical -> {response.status_code}")

    response = client.get("/api/cards/domain-stats")
    print(f"   GET /api/cards/domain-stats -> {response.status_code}")

    return response.status_code == 200


def test_bosses_api():
    """测试Boss API"""
    print("\n" + "=" * 60)
    print("测试 /api/bosses 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/bosses")
    print(f"   GET /api/bosses -> {response.status_code}")

    return response.status_code == 200


def test_npcs_api():
    """测试NPC API"""
    print("\n" + "=" * 60)
    print("测试 /api/npcs 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/npcs")
    print(f"   GET /api/npcs -> {response.status_code}")

    response = client.get("/api/npcs/unlocked")
    print(f"   GET /api/npcs/unlocked -> {response.status_code}")

    return response.status_code == 200


def test_questions_api():
    """测试题目API"""
    print("\n" + "=" * 60)
    print("测试 /api/questions 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/questions")
    print(f"   GET /api/questions -> {response.status_code}")

    return response.status_code == 200


def test_dashboard_api():
    """测试仪表盘API"""
    print("\n" + "=" * 60)
    print("测试 /api/dashboard 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/dashboard/today-review")
    print(f"   GET /api/dashboard/today-review -> {response.status_code}")

    response = client.get("/api/dashboard/stats")
    print(f"   GET /api/dashboard/stats -> {response.status_code}")

    response = client.get("/api/dashboard/new-user-status")
    print(f"   GET /api/dashboard/new-user-status -> {response.status_code}")

    return response.status_code == 200


def test_learning_api():
    """测试学习API"""
    print("\n" + "=" * 60)
    print("测试 /api/learning 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/learning/topics")
    print(f"   GET /api/learning/topics -> {response.status_code}")

    return response.status_code == 200


def test_settings_api():
    """测试设置API"""
    print("\n" + "=" * 60)
    print("测试 /api/settings 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/settings")
    print(f"   GET /api/settings -> {response.status_code}")

    return response.status_code == 200


def test_boss_battle_api():
    """测试Boss战API"""
    print("\n" + "=" * 60)
    print("测试 /api/boss, /api/battle 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/boss/1")
    print(f"   GET /api/boss/1 -> {response.status_code}")

    response = client.post("/api/boss/generate", json={"card_id": 1})
    print(f"   POST /api/boss/generate -> {response.status_code}")

    response = client.post("/api/battle/start", json={"boss_id": 1, "card_ids": [1]})
    print(f"   POST /api/battle/start -> {response.status_code}")

    response = client.get("/api/battle/1/result")
    print(f"   GET /api/battle/1/result -> {response.status_code}")

    return True


def test_tasks_api():
    """测试任务API"""
    print("\n" + "=" * 60)
    print("测试 /api/tasks 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/tasks/daily")
    print(f"   GET /api/tasks/daily -> {response.status_code}")

    response = client.get("/api/tasks/upcoming")
    print(f"   GET /api/tasks/upcoming -> {response.status_code}")

    return response.status_code == 200


def test_dialogue_api():
    """测试对话API"""
    print("\n" + "=" * 60)
    print("测试 /api/dialogue 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.post("/api/dialogue/start", json={"npc_id": 1})
    print(f"   POST /api/dialogue/start -> {response.status_code}")

    response = client.get("/api/dialogue/1/history")
    print(f"   GET /api/dialogue/1/history -> {response.status_code}")

    return True


def test_user_api():
    """测试用户API"""
    print("\n" + "=" * 60)
    print("测试 /api/user 路由")
    print("=" * 60)

    app = AlgomateApp()
    client = TestClient(app.api_app)

    response = client.get("/api/user")
    print(f"   GET /api/user -> {response.status_code}")

    response = client.get("/api/user/stats")
    print(f"   GET /api/user/stats -> {response.status_code}")

    return response.status_code == 200


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Algomate API 测试")
    print("=" * 60)

    results = []

    results.append(("API路由注册", test_api_registration()))
    results.append(("/api/notes", test_notes_api()))
    results.append(("/api/cards", test_cards_api()))
    results.append(("/api/bosses", test_bosses_api()))
    results.append(("/api/npcs", test_npcs_api()))
    results.append(("/api/questions", test_questions_api()))
    results.append(("/api/dashboard", test_dashboard_api()))
    results.append(("/api/learning", test_learning_api()))
    results.append(("/api/settings", test_settings_api()))
    results.append(("/api/boss & /api/battle", test_boss_battle_api()))
    results.append(("/api/tasks", test_tasks_api()))
    results.append(("/api/dialogue", test_dialogue_api()))
    results.append(("/api/user", test_user_api()))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"   {status} {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("所有测试通过！")
    else:
        print("部分测试失败，请检查上述输出。")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

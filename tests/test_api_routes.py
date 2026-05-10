import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi.testclient import TestClient
from algomate.main import AlgomateApp


def test_api_registration():
    app = AlgomateApp()
    client = TestClient(app.api_app)

    routes = [route.path for route in app.api_app.routes]

    expected_prefixes = [
        "/api/v1/cards",
        "/api/v1/bosses",
        "/api/v1/npcs",
        "/api/v1/dialogues",
        "/api/v1/practice",
        "/api/v1/progress",
        "/api/v1/settings",
        "/api/v1/dashboard",
        "/api/v1/learning",
        "/api/v1/tasks",
        "/api/v1/users",
        "/api/v1/realms",
        "/api/v1/reviews",
        "/api/v1/stats",
        "/api/v1/algorithm-info",
        "/api/notes",
        "/api/questions",
        "/api/review-records",
        "/api/learning-progress",
    ]

    missing_routes = []
    for prefix in expected_prefixes:
        found = any(route.startswith(prefix) for route in routes)
        if not found:
            missing_routes.append(prefix)

    assert not missing_routes, f"缺少以下路由: {missing_routes}"


def test_cards_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/cards")
    assert response.status_code == 200


def test_bosses_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/bosses")
    assert response.status_code == 200


def test_npcs_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/npcs")
    assert response.status_code == 200


def test_dashboard_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/dashboard/today-review")
    assert response.status_code == 200


def test_learning_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/learning/topics")
    assert response.status_code == 200


def test_settings_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/settings")
    assert response.status_code == 200


def test_tasks_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200


def test_users_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/users")
    assert response.status_code == 200


def test_realms_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/realms")
    assert response.status_code == 200


def test_stats_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/stats/overview")
    assert response.status_code == 200


def test_algorithm_info_api():
    app = AlgomateApp()
    client = TestClient(app.api_app)
    response = client.get("/api/v1/algorithm-info")
    assert response.status_code == 200

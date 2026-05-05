import sys
import os

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, "f:\\workspace\\python\\algomate\\src")
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LLM_API_KEY'] = ''

from fastapi.testclient import TestClient
from algomate.main import AlgomateApp
from algomate.config.settings import AppConfig
from algomate.data.database import Database
import tempfile


def _create_client():
    Database._instance = None
    AppConfig._instance = None
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    config = AppConfig(DB_PATH=tmp.name, LLM_API_KEY="")
    app = AlgomateApp(config=config)
    return TestClient(app.api_app), tmp.name


def test_stats_overview_no_cards():
    client, db_path = _create_client()
    try:
        response = client.get("/api/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_cards" in data
        assert data["total_cards"] == 0
        assert "total_realms" in data
        assert "consecutive_days" in data
    finally:
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_npc_novice_forest():
    client, db_path = _create_client()
    try:
        from algomate.api.routes import _init_default_npcs
        _init_default_npcs()
        response = client.get("/api/npc/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "老夫子"
        assert data["domain"] == "基础数据结构"
        assert "topics" in data
    finally:
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_cards_empty_list():
    client, db_path = _create_client()
    try:
        response = client.get("/api/cards/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    finally:
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_algorithm_info():
    client, db_path = _create_client()
    try:
        response = client.get("/api/algorithm-info")
        assert response.status_code == 200
        data = response.json()
        assert "topic_prerequisites" in data
        assert "topic_importance" in data
        assert "algorithm_categories" in data
        assert isinstance(data["topic_prerequisites"], dict)
        assert isinstance(data["topic_importance"], dict)
        assert isinstance(data["algorithm_categories"], dict)
    finally:
        try:
            os.unlink(db_path)
        except OSError:
            pass

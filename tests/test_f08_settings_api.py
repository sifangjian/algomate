import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from algomate.data.database import Base, Database, _ensure_models_imported
from algomate.models.user_settings import UserSetting


_ensure_models_imported()


class _InMemoryDatabase:
    def __init__(self, engine):
        self.engine = engine
        self.SessionLocal = sessionmaker(bind=engine)

    def get_session(self):
        return self.SessionLocal()


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_db(db_engine):
    return _InMemoryDatabase(db_engine)


@pytest.fixture
def client(test_db):
    original_get_instance = Database.get_instance
    original_instance = Database._instance
    Database._instance = test_db
    Database.get_instance = classmethod(lambda cls, config=None: test_db)

    from algomate.config.settings import AppConfig

    original_appconfig_load = AppConfig.load
    original_appconfig_instance = AppConfig._instance

    with patch.object(Path, 'mkdir'):
        test_config = AppConfig()
        test_config.LLM_API_KEY = ""
        AppConfig._instance = test_config
        AppConfig.load = classmethod(lambda cls, *a, **kw: test_config)

        from algomate.main import AlgomateApp
        with patch('algomate.main.setup_logging'):
            app = AlgomateApp(config=test_config)
            test_client = TestClient(app.api_app)

    yield test_client

    Database.get_instance = original_get_instance
    Database._instance = original_instance
    AppConfig.load = original_appconfig_load
    AppConfig._instance = original_appconfig_instance


class TestGetSettingsAPI:
    def test_get_settings_returns_defaults(self, client):
        response = client.get("/api/v1/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["onboarding_completed"] is False
        assert data["data"]["api_key_configured"] is False
        assert data["data"]["theme"] == "light"
        assert data["data"]["language"] == "zh-CN"

    def test_get_settings_after_onboarding_completed(self, client, db_engine):
        Session = sessionmaker(bind=db_engine)
        session = Session()
        session.add(UserSetting(key="onboarding_completed", value="true"))
        session.commit()
        session.close()

        response = client.get("/api/v1/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["onboarding_completed"] is True

    def test_get_settings_does_not_return_api_key(self, client, db_engine):
        Session = sessionmaker(bind=db_engine)
        session = Session()
        session.add(UserSetting(key="api_key", value="secret-key-123"))
        session.commit()
        session.close()

        response = client.get("/api/v1/settings")
        assert response.status_code == 200
        data = response.json()
        assert "api_key" not in data["data"]


class TestUpdateSettingsAPI:
    def test_update_onboarding_completed(self, client):
        response = client.put("/api/v1/settings", json={"onboarding_completed": True})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["updated"] is True

        get_response = client.get("/api/v1/settings")
        assert get_response.json()["data"]["onboarding_completed"] is True

    def test_update_onboarding_cannot_revert(self, client):
        client.put("/api/v1/settings", json={"onboarding_completed": True})

        response = client.put("/api/v1/settings", json={"onboarding_completed": False})
        assert response.status_code == 200

        get_response = client.get("/api/v1/settings")
        assert get_response.json()["data"]["onboarding_completed"] is True

    def test_update_theme(self, client):
        response = client.put("/api/v1/settings", json={"theme": "dark"})
        assert response.status_code == 200

        get_response = client.get("/api/v1/settings")
        assert get_response.json()["data"]["theme"] == "dark"

    def test_update_invalid_theme(self, client):
        response = client.put("/api/v1/settings", json={"theme": "invalid"})
        assert response.status_code == 400

    def test_update_partial_settings(self, client):
        response = client.put("/api/v1/settings", json={"theme": "dark"})
        assert response.status_code == 200

        get_response = client.get("/api/v1/settings")
        data = get_response.json()["data"]
        assert data["theme"] == "dark"
        assert data["onboarding_completed"] is False
        assert data["language"] == "zh-CN"

    def test_update_language(self, client):
        response = client.put("/api/v1/settings", json={"language": "en-US"})
        assert response.status_code == 200

        get_response = client.get("/api/v1/settings")
        assert get_response.json()["data"]["language"] == "en-US"

    def test_update_empty_body(self, client):
        response = client.put("/api/v1/settings", json={})
        assert response.status_code == 200

        get_response = client.get("/api/v1/settings")
        data = get_response.json()["data"]
        assert data["onboarding_completed"] is False
        assert data["theme"] == "light"

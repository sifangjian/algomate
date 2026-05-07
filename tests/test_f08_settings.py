import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from algomate.data.database import Base, _ensure_models_imported
from algomate.models.user_settings import UserSetting


_ensure_models_imported()


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
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


class TestUserSettingModel:
    def test_create_onboarding_completed(self, db_session):
        setting = UserSetting(key="onboarding_completed", value="true")
        db_session.add(setting)
        db_session.commit()
        db_session.refresh(setting)

        assert setting.id is not None
        assert setting.key == "onboarding_completed"
        assert setting.value == "true"

    def test_query_onboarding_completed(self, db_session):
        setting = UserSetting(key="onboarding_completed", value="true")
        db_session.add(setting)
        db_session.commit()

        result = db_session.query(UserSetting).filter(
            UserSetting.key == "onboarding_completed"
        ).first()

        assert result is not None
        assert result.value == "true"

    def test_query_nonexistent_key_returns_none(self, db_session):
        result = db_session.query(UserSetting).filter(
            UserSetting.key == "onboarding_completed"
        ).first()

        assert result is None

    def test_update_onboarding_completed(self, db_session):
        setting = UserSetting(key="onboarding_completed", value="false")
        db_session.add(setting)
        db_session.commit()

        setting.value = "true"
        setting.updated_at = datetime.now()
        db_session.commit()
        db_session.refresh(setting)

        assert setting.value == "true"

    def test_key_is_unique(self, db_session):
        setting1 = UserSetting(key="onboarding_completed", value="false")
        db_session.add(setting1)
        db_session.commit()

        setting2 = UserSetting(key="onboarding_completed", value="true")
        db_session.add(setting2)

        with pytest.raises(Exception):
            db_session.commit()

    def test_multiple_settings(self, db_session):
        settings = [
            UserSetting(key="onboarding_completed", value="false"),
            UserSetting(key="theme", value="light"),
            UserSetting(key="language", value="zh-CN"),
        ]
        for s in settings:
            db_session.add(s)
        db_session.commit()

        all_settings = db_session.query(UserSetting).all()
        assert len(all_settings) == 3

        result = {s.key: s.value for s in all_settings}
        assert result["onboarding_completed"] == "false"
        assert result["theme"] == "light"
        assert result["language"] == "zh-CN"


class TestSettingsRepository:
    def test_get_settings_returns_defaults_when_empty(self, db_session):
        from algomate.data.repositories.settings_repo import SettingsRepository

        repo = SettingsRepository(db_session)
        settings = repo.get_settings()

        assert settings["onboarding_completed"] is False
        assert settings["api_key_configured"] is False
        assert settings["theme"] == "light"
        assert settings["language"] == "zh-CN"

    def test_get_settings_returns_stored_values(self, db_session):
        from algomate.data.repositories.settings_repo import SettingsRepository

        db_session.add(UserSetting(key="onboarding_completed", value="true"))
        db_session.add(UserSetting(key="theme", value="dark"))
        db_session.commit()

        repo = SettingsRepository(db_session)
        settings = repo.get_settings()

        assert settings["onboarding_completed"] is True
        assert settings["theme"] == "dark"

    def test_is_onboarding_completed_default_false(self, db_session):
        from algomate.data.repositories.settings_repo import SettingsRepository

        repo = SettingsRepository(db_session)
        assert repo.is_onboarding_completed() is False

    def test_is_onboarding_completed_true(self, db_session):
        from algomate.data.repositories.settings_repo import SettingsRepository

        db_session.add(UserSetting(key="onboarding_completed", value="true"))
        db_session.commit()

        repo = SettingsRepository(db_session)
        assert repo.is_onboarding_completed() is True

    def test_complete_onboarding(self, db_session):
        from algomate.data.repositories.settings_repo import SettingsRepository

        repo = SettingsRepository(db_session)
        repo.complete_onboarding()

        assert repo.is_onboarding_completed() is True

        result = db_session.query(UserSetting).filter(
            UserSetting.key == "onboarding_completed"
        ).first()
        assert result is not None
        assert result.value == "true"

    def test_onboarding_cannot_revert(self, db_session):
        from algomate.data.repositories.settings_repo import SettingsRepository

        repo = SettingsRepository(db_session)
        repo.complete_onboarding()

        repo.update_settings({"onboarding_completed": False})

        assert repo.is_onboarding_completed() is True

    def test_update_settings_theme(self, db_session):
        from algomate.data.repositories.settings_repo import SettingsRepository

        repo = SettingsRepository(db_session)
        repo.update_settings({"theme": "dark"})

        settings = repo.get_settings()
        assert settings["theme"] == "dark"

    def test_update_settings_invalid_theme(self, db_session):
        from algomate.data.repositories.settings_repo import SettingsRepository

        repo = SettingsRepository(db_session)

        with pytest.raises(ValueError, match="Invalid theme"):
            repo.update_settings({"theme": "invalid"})

    def test_update_settings_partial(self, db_session):
        from algomate.data.repositories.settings_repo import SettingsRepository

        repo = SettingsRepository(db_session)
        repo.update_settings({"theme": "dark"})

        settings = repo.get_settings()
        assert settings["theme"] == "dark"
        assert settings["onboarding_completed"] is False
        assert settings["language"] == "zh-CN"

    def test_update_settings_api_key_configured(self, db_session):
        from algomate.data.repositories.settings_repo import SettingsRepository

        repo = SettingsRepository(db_session)
        repo.update_settings({"api_key_configured": True})

        settings = repo.get_settings()
        assert settings["api_key_configured"] is True

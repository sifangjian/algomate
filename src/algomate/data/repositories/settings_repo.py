from datetime import datetime
from typing import Dict, Any

from algomate.models.user_settings import UserSetting


DEFAULT_SETTINGS = {
    "onboarding_completed": "false",
    "api_key_configured": "false",
    "theme": "light",
    "language": "zh-CN",
}

BOOLEAN_KEYS = {"onboarding_completed", "api_key_configured"}

VALID_THEMES = {"light", "dark"}


class SettingsRepository:

    def __init__(self, session):
        self.session = session

    def get_settings(self) -> Dict[str, Any]:
        settings = self.session.query(UserSetting).all()
        settings_dict = {s.key: s.value for s in settings}

        result = {}
        for key, default_value in DEFAULT_SETTINGS.items():
            raw_value = settings_dict.get(key, default_value)
            if key in BOOLEAN_KEYS:
                result[key] = raw_value.lower() == "true"
            else:
                result[key] = raw_value

        return result

    def is_onboarding_completed(self) -> bool:
        setting = self.session.query(UserSetting).filter(
            UserSetting.key == "onboarding_completed"
        ).first()

        if setting is None:
            return False

        return setting.value.lower() == "true"

    def complete_onboarding(self) -> None:
        setting = self.session.query(UserSetting).filter(
            UserSetting.key == "onboarding_completed"
        ).first()

        if setting is None:
            setting = UserSetting(key="onboarding_completed", value="true")
            self.session.add(setting)
        else:
            setting.value = "true"
            setting.updated_at = datetime.now()

        self.session.commit()

    def update_settings(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        if "theme" in update_data:
            if update_data["theme"] not in VALID_THEMES:
                raise ValueError(f"Invalid theme: {update_data['theme']}")

        if "onboarding_completed" in update_data:
            new_value = update_data["onboarding_completed"]
            if new_value:
                self._upsert("onboarding_completed", "true")
            elif not self.is_onboarding_completed():
                self._upsert("onboarding_completed", str(new_value).lower())

        if "theme" in update_data:
            self._upsert("theme", update_data["theme"])

        if "language" in update_data:
            self._upsert("language", update_data["language"])

        if "api_key_configured" in update_data:
            self._upsert("api_key_configured", str(update_data["api_key_configured"]).lower())

        self.session.commit()
        return {"updated": True}

    def _upsert(self, key: str, value: str) -> None:
        setting = self.session.query(UserSetting).filter(
            UserSetting.key == key
        ).first()

        if setting is None:
            setting = UserSetting(key=key, value=value)
            self.session.add(setting)
        else:
            setting.value = value
            setting.updated_at = datetime.now()

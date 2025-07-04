"""
Конфігурація для Instagram Bot
"""

import os
import json
from typing import Dict, List, Any

class BotConfig:
    """Клас для управління конфігурацією бота"""
    
    def __init__(self, config_file: str = "bot_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Завантаження конфігурації"""
        default_config = {
            "captcha_api_key": "",
            "proxy_list": [],
            "max_accounts": 10,
            "daily_action_limit": 100,
            "action_delays": {
                "like": [2, 5],
                "comment": [3, 8],
                "follow": [4, 10],
                "story_view": [1, 3],
                "story_reply": [2, 6]
            },
            "user_agents": [
                "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
                "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
            ],
            "story_replies": [
                "🔥🔥🔥", "❤️", "Круто!", "👍", "Супер!", 
                "💯", "🙌", "Класно!", "👏", "Wow!",
                "Дуже цікаво!", "Топ контент!", "Красиво!"
            ],
            "automation_settings": {
                "run_schedule": "09:00-22:00",
                "break_duration": [30, 120],
                "max_actions_per_hour": 20,
                "rotate_accounts": True,
                "use_proxy_rotation": True
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            else:
                self.save_config(default_config)
        except Exception as e:
            print(f"Помилка завантаження конфігурації: {e}")
        
        return default_config
    
    def save_config(self, config: Dict[str, Any] = None):
        """Збереження конфігурації"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Помилка збереження конфігурації: {e}")
    
    def get(self, key: str, default=None):
        """Отримання значення з конфігурації"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Встановлення значення в конфігурації"""
        self.config[key] = value
        self.save_config()
    
    def get_story_replies(self) -> List[str]:
        """Отримання шаблонів відповідей для сторіс"""
        return self.config.get('story_replies', [])
    
    def get_automation_settings(self) -> Dict[str, Any]:
        """Отримання налаштувань автоматизації"""
        return self.config.get('automation_settings', {})
    
    def export_config(self, file_path: str):
        """Експорт конфігурації у файл"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Помилка експорту конфігурації: {e}")
            return False
    
    def import_config(self, file_path: str):
        """Імпорт конфігурації з файлу"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            self.config.update(imported_config)
            self.save_config()
            return True
        except Exception as e:
            print(f"Помилка імпорту конфігурації: {e}")
            return False
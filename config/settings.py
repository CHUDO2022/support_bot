# -*- coding: utf-8 -*-
"""
Модуль конфигурации приложения
Централизованное управление всеми настройками
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from bot.behavior import HumanBehaviorConfig

# Загружаем .env файл (явно указываем путь)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    # Пробуем загрузить из текущей директории
    load_dotenv(override=True)


@dataclass(frozen=True)
class OpenAISettings:
    """Настройки OpenAI API"""
    api_key: str
    assistant_id: str
    
    @classmethod
    def from_env(cls) -> "OpenAISettings":
        """Создает настройки OpenAI из переменных окружения"""
        # Проверяем наличие .env файла
        env_path = Path(__file__).parent.parent / ".env"
        if not env_path.exists():
            raise ValueError(
                f"❌ Файл .env не найден!\n"
                f"📁 Ожидаемый путь: {env_path.absolute()}\n"
                f"📋 Создайте файл .env в корневой директории проекта.\n"
                f"💡 Скопируйте env_example.txt в .env и заполните настройки."
            )
        
        # Перезагружаем .env файл для надежности
        # load_dotenv может вернуть False, если файл пустой или не содержит переменных,
        # но это не критично - мы проверим переменные отдельно
        try:
            load_dotenv(dotenv_path=env_path, override=True)
        except Exception as e:
            raise ValueError(
                f"❌ Ошибка при загрузке файла .env!\n"
                f"📁 Путь: {env_path.absolute()}\n"
                f"🔍 Ошибка: {str(e)}\n"
                f"💡 Проверьте, что файл существует и доступен для чтения."
            )
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.strip() in ("your_openai_api_key_here", ""):
            raise ValueError(
                f"❌ OPENAI_API_KEY не найден или не заполнен!\n"
                f"📁 Файл: {env_path.absolute()}\n"
                f"💡 Откройте файл .env и заполните OPENAI_API_KEY вашим реальным ключом.\n"
                f"🔑 Получите ключ на https://platform.openai.com/api-keys"
            )
        
        assistant_id = os.getenv("ASSISTANT_ID")
        if not assistant_id or assistant_id.strip() in ("your_assistant_id_here", ""):
            raise ValueError(
                f"❌ ASSISTANT_ID не найден или не заполнен!\n"
                f"📁 Файл: {env_path.absolute()}\n"
                f"💡 Откройте файл .env и заполните ASSISTANT_ID.\n"
                f"🤖 Создайте Assistant на https://platform.openai.com/assistants"
            )
        
        return cls(api_key=api_key.strip(), assistant_id=assistant_id.strip())


@dataclass(frozen=True)
class TelegramSettings:
    """Настройки Telegram API"""
    api_id: int
    api_hash: str
    bot_name: str
    
    @classmethod
    def from_env(cls) -> "TelegramSettings":
        """Создает настройки Telegram из переменных окружения"""
        api_id = os.getenv("TELEGRAM_API_ID")
        if not api_id:
            raise ValueError("TELEGRAM_API_ID не найден в переменных окружения")
        
        try:
            api_id_int = int(api_id)
        except ValueError:
            raise ValueError(f"TELEGRAM_API_ID должен быть числом, получено: {api_id}")
        
        api_hash = os.getenv("TELEGRAM_API_HASH")
        if not api_hash:
            raise ValueError("TELEGRAM_API_HASH не найден в переменных окружения")
        
        bot_name = os.getenv("BOT_NAME", "support_bot_v4")
        
        return cls(api_id=api_id_int, api_hash=api_hash, bot_name=bot_name)


@dataclass(frozen=True)
class BotSettings:
    """Настройки бота"""
    threads_file: str = "threads.json"
    bot_state_file: str = "bot_state.json"
    log_level: str = "INFO"
    human_behavior_enabled: bool = True
    
    @property
    def log_level_int(self) -> int:
        """Преобразует строковый уровень логирования в int"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(self.log_level.upper(), logging.INFO)
    
    @property
    def human_behavior_config(self) -> HumanBehaviorConfig:
        """Создает конфигурацию человеческого поведения"""
        return HumanBehaviorConfig(
            min_typing_speed=0.8,
            max_typing_speed=2.5,
            thinking_pause_min=2.0,
            thinking_pause_max=6.0,
            correction_pause=2.0,
            emoji_probability=0.3,
            micro_reaction_probability=0.3,
            emotional_response_probability=0.2,
            max_message_length=200,
            split_probability=0.3,
            connector_probability=0.2,
            typo_probability=0.05,
            self_correction_probability=0.3,
            hesitation_probability=0.2
        )
    
    @classmethod
    def from_env(cls) -> "BotSettings":
        """Создает настройки бота из переменных окружения"""
        return cls(
            threads_file=os.getenv("THREADS_FILE", "threads.json"),
            bot_state_file=os.getenv("BOT_STATE_FILE", "bot_state.json"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            human_behavior_enabled=os.getenv("HUMAN_BEHAVIOR_ENABLED", "true").lower() == "true",
        )


@dataclass(frozen=True)
class Settings:
    """Общие настройки приложения"""
    openai: OpenAISettings
    telegram: TelegramSettings
    bot: BotSettings
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Создает настройки из переменных окружения"""
        return cls(
            openai=OpenAISettings.from_env(),
            telegram=TelegramSettings.from_env(),
            bot=BotSettings.from_env(),
        )
    
    def validate(self) -> None:
        """Валидирует настройки"""
        # Проверяем наличие необходимых файлов и создаем директории при необходимости
        threads_dir = Path(self.bot.threads_file).parent
        if threads_dir and not threads_dir.exists():
            threads_dir.mkdir(parents=True, exist_ok=True)
        
        state_dir = Path(self.bot.bot_state_file).parent
        if state_dir and not state_dir.exists():
            state_dir.mkdir(parents=True, exist_ok=True)


# Глобальный экземпляр настроек (singleton pattern)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Получает глобальный экземпляр настроек (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
        _settings.validate()
    return _settings


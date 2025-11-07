# -*- coding: utf-8 -*-
"""
Хранилище для состояния бота
"""
import json
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class StateStorage:
    """Управление хранением состояния бота"""
    
    def __init__(self, file_path: str):
        """
        Инициализация хранилища
        
        Args:
            file_path: Путь к файлу для хранения состояния
        """
        self.file_path = Path(file_path)
        self._state: Dict = {
            "global_enabled": True,
            "blacklisted_chats": {
                "by_id": [],
                "by_username": [],
                "by_title": []
            },
            "admin_users": []
        }
        self._load()
    
    def _load(self) -> None:
        """Загружает состояние из файла"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    loaded_state = json.load(f)
                
                # Миграция старого формата blacklist
                if "blacklisted_chats" in loaded_state:
                    if isinstance(loaded_state["blacklisted_chats"], list):
                        logger.info("Миграция старого формата blacklist в новый")
                        old_blacklist = loaded_state["blacklisted_chats"]
                        loaded_state["blacklisted_chats"] = {
                            "by_id": old_blacklist,
                            "by_username": [],
                            "by_title": []
                        }
                        # Сохраняем миграцию
                        self._state.update(loaded_state)
                        self.save()
                    else:
                        self._state.update(loaded_state)
                else:
                    self._state.update(loaded_state)
                
                logger.info(f"Загружено состояние из {self.file_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON в {self.file_path}: {e}")
            except Exception as e:
                logger.error(f"Ошибка загрузки состояния: {e}")
        else:
            # Создаем директорию, если нужно
            if self.file_path.parent:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Файл {self.file_path} не существует, будет создан при первом сохранении")
    
    def save(self) -> None:
        """Сохраняет состояние в файл"""
        try:
            # Создаем директорию, если нужно
            if self.file_path.parent:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
            logger.debug(f"Сохранено состояние в {self.file_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения состояния: {e}")
            raise
    
    def is_global_enabled(self) -> bool:
        """Проверяет, включен ли бот глобально"""
        return self._state.get("global_enabled", True)
    
    def set_global_enabled(self, enabled: bool, save: bool = True) -> None:
        """Устанавливает глобальное состояние бота"""
        self._state["global_enabled"] = enabled
        if save:
            self.save()
    
    def is_bot_active_in_chat(
        self, 
        chat_id: int, 
        chat_username: Optional[str] = None, 
        chat_title: Optional[str] = None
    ) -> bool:
        """Проверяет, активен ли бот в конкретном чате"""
        if not self.is_global_enabled():
            return False
        
        blacklist = self._state.get("blacklisted_chats", {})
        if not isinstance(blacklist, dict):
            logger.warning("Некорректная структура blacklisted_chats, сброс к значению по умолчанию")
            self._state["blacklisted_chats"] = {"by_id": [], "by_username": [], "by_title": []}
            self.save()
            return True
        
        # Проверка по ID
        if chat_id in blacklist.get("by_id", []):
            return False
        
        # Проверка по username
        if chat_username and chat_username in blacklist.get("by_username", []):
            return False
        
        # Проверка по title
        if chat_title and chat_title in blacklist.get("by_title", []):
            return False
        
        return True
    
    def is_user_blocked(self, user_id: int, user_username: Optional[str] = None) -> bool:
        """Проверяет, заблокирован ли пользователь"""
        blacklist = self._state.get("blacklisted_chats", {})
        
        # Проверка по ID
        if user_id in blacklist.get("by_id", []):
            return True
        
        # Проверка по username
        if user_username and f"@{user_username}" in blacklist.get("by_username", []):
            return True
        
        return False
    
    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь админом"""
        admin_users = self._state.get("admin_users", [])
        # Если список админов пуст, все пользователи считаются админами
        return len(admin_users) == 0 or user_id in admin_users
    
    def get_blacklist_stats(self) -> Dict[str, int]:
        """Возвращает статистику черного списка"""
        blacklist = self._state.get("blacklisted_chats", {})
        return {
            "by_id": len(blacklist.get("by_id", [])),
            "by_username": len(blacklist.get("by_username", [])),
            "by_title": len(blacklist.get("by_title", []))
        }
    
    def get_state(self) -> Dict:
        """Получает полное состояние (для обратной совместимости)"""
        return self._state.copy()
    
    def update_state(self, updates: Dict, save: bool = True) -> None:
        """Обновляет состояние"""
        self._state.update(updates)
        if save:
            self.save()


# -*- coding: utf-8 -*-
"""
Хранилище для thread ID пользователей
"""
import json
import os
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ThreadStorage:
    """Управление хранением thread ID для пользователей"""
    
    def __init__(self, file_path: str):
        """
        Инициализация хранилища
        
        Args:
            file_path: Путь к файлу для хранения threads
        """
        self.file_path = Path(file_path)
        self._cache: Dict[str, str] = {}
        self._load()
    
    def _load(self) -> None:
        """Загружает threads из файла"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                logger.info(f"Загружено {len(self._cache)} threads из {self.file_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON в {self.file_path}: {e}")
                self._cache = {}
            except Exception as e:
                logger.error(f"Ошибка загрузки threads: {e}")
                self._cache = {}
        else:
            # Создаем директорию, если нужно
            if self.file_path.parent:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Файл {self.file_path} не существует, будет создан при первом сохранении")
    
    def save(self) -> None:
        """Сохраняет threads в файл"""
        try:
            # Создаем директорию, если нужно
            if self.file_path.parent:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"Сохранено {len(self._cache)} threads в {self.file_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения threads: {e}")
            raise
    
    def get(self, user_id: str) -> Optional[str]:
        """
        Получает thread ID для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Thread ID или None, если не найден
        """
        return self._cache.get(user_id)
    
    def set(self, user_id: str, thread_id: str, save: bool = True) -> None:
        """
        Устанавливает thread ID для пользователя
        
        Args:
            user_id: ID пользователя
            thread_id: Thread ID
            save: Сохранять ли сразу в файл
        """
        self._cache[user_id] = thread_id
        if save:
            self.save()
    
    def delete(self, user_id: str, save: bool = True) -> None:
        """
        Удаляет thread ID для пользователя
        
        Args:
            user_id: ID пользователя
            save: Сохранять ли сразу в файл
        """
        if user_id in self._cache:
            del self._cache[user_id]
            if save:
                self.save()
    
    def get_all(self) -> Dict[str, str]:
        """
        Получает все threads
        
        Returns:
            Словарь всех threads
        """
        return self._cache.copy()
    
    def clear(self, save: bool = True) -> None:
        """
        Очищает все threads
        
        Args:
            save: Сохранять ли сразу в файл
        """
        self._cache.clear()
        if save:
            self.save()
    
    def __len__(self) -> int:
        """Возвращает количество threads"""
        return len(self._cache)



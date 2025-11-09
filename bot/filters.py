"""
Модуль для фильтрации дубликатов сообщений
Предотвращает обработку однотипных сообщений от пользователей
"""

import hashlib
import time
import logging
from typing import Dict, Set, Optional
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class DuplicateMessageFilter:
    """Фильтр для блокировки дубликатов сообщений"""
    
    def __init__(self, 
                 time_window: int = 300,  # 5 минут
                 max_messages_per_user: int = 10,
                 similarity_threshold: float = 0.8):
        """
        Инициализация фильтра
        
        Args:
            time_window: Время в секундах для отслеживания сообщений
            max_messages_per_user: Максимальное количество сообщений на пользователя
            similarity_threshold: Порог схожести для определения дубликатов (0.0-1.0)
        """
        self.time_window = time_window
        self.max_messages_per_user = max_messages_per_user
        self.similarity_threshold = similarity_threshold
        
        # Кэш сообщений пользователей: user_id -> deque(timestamp, message_hash, text)
        self.user_messages: Dict[int, deque] = defaultdict(lambda: deque(maxlen=max_messages_per_user))
        
        # Хэши сообщений для быстрого поиска
        self.message_hashes: Set[str] = set()
        
        # Статистика
        self.blocked_count = 0
        self.total_processed = 0
        
        logger.info(f"Duplicate filter initialized: time_window={time_window}s, "
                   f"max_messages={max_messages_per_user}, threshold={similarity_threshold}")

    def _normalize_text(self, text: str) -> str:
        """
        Нормализует текст для сравнения
        
        Args:
            text: Исходный текст
            
        Returns:
            str: Нормализованный текст
        """
        if not text:
            return ""
        
        # Приводим к нижнему регистру
        normalized = text.lower().strip()
        
        # Удаляем лишние пробелы
        normalized = ' '.join(normalized.split())
        
        # Удаляем знаки препинания для лучшего сравнения
        import re
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Вычисляет схожесть между двумя текстами
        
        Args:
            text1: Первый текст
            text2: Второй текст
            
        Returns:
            float: Коэффициент схожести (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Нормализуем тексты
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        if norm1 == norm2:
            return 1.0
        
        # Простое сравнение по словам
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Вычисляем коэффициент Жаккара
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def _cleanup_old_messages(self, user_id: int, current_time: float) -> None:
        """
        Удаляет старые сообщения из кэша пользователя
        
        Args:
            user_id: ID пользователя
            current_time: Текущее время
        """
        user_deque = self.user_messages[user_id]
        
        # Удаляем сообщения старше time_window
        while user_deque and current_time - user_deque[0][0] > self.time_window:
            old_timestamp, old_hash, old_text = user_deque.popleft()
            self.message_hashes.discard(old_hash)
            logger.debug(f"Removed old message from user {user_id}: {old_text[:50]}...")

    def is_duplicate(self, user_id: int, message_text: str) -> bool:
        """
        Проверяет, является ли сообщение дубликатом
        
        Args:
            user_id: ID пользователя
            message_text: Текст сообщения
            
        Returns:
            bool: True если сообщение является дубликатом
        """
        self.total_processed += 1
        current_time = time.time()
        
        # Очищаем старые сообщения
        self._cleanup_old_messages(user_id, current_time)
        
        # Нормализуем текст
        normalized_text = self._normalize_text(message_text)
        
        if not normalized_text:
            logger.debug(f"Empty message from user {user_id}, allowing")
            return False
        
        # Создаем хэш сообщения
        message_hash = hashlib.md5(normalized_text.encode('utf-8')).hexdigest()
        
        # Проверяем точное совпадение
        if message_hash in self.message_hashes:
            logger.info(f"Exact duplicate detected from user {user_id}: {message_text[:50]}...")
            self.blocked_count += 1
            return True
        
        # Проверяем схожесть с предыдущими сообщениями пользователя
        user_deque = self.user_messages[user_id]
        
        for timestamp, msg_hash, msg_text in user_deque:
            similarity = self._calculate_similarity(message_text, msg_text)
            
            if similarity >= self.similarity_threshold:
                logger.info(f"Similar message detected from user {user_id} "
                          f"(similarity: {similarity:.2f}): {message_text[:50]}...")
                self.blocked_count += 1
                return True
        
        # Добавляем сообщение в кэш
        user_deque.append((current_time, message_hash, message_text))
        self.message_hashes.add(message_hash)
        
        logger.debug(f"New message from user {user_id} added to cache: {message_text[:50]}...")
        return False

    def get_stats(self) -> Dict[str, int]:
        """
        Возвращает статистику работы фильтра
        
        Returns:
            Dict[str, int]: Статистика
        """
        return {
            "total_processed": self.total_processed,
            "blocked_count": self.blocked_count,
            "active_users": len(self.user_messages),
            "cached_messages": sum(len(deque) for deque in self.user_messages.values())
        }

    def clear_user_cache(self, user_id: int) -> None:
        """
        Очищает кэш сообщений для конкретного пользователя
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self.user_messages:
            # Удаляем хэши сообщений пользователя
            for _, msg_hash, _ in self.user_messages[user_id]:
                self.message_hashes.discard(msg_hash)
            
            # Очищаем кэш пользователя
            self.user_messages[user_id].clear()
            logger.info(f"Cleared cache for user {user_id}")

    def clear_all_cache(self) -> None:
        """Очищает весь кэш"""
        self.user_messages.clear()
        self.message_hashes.clear()
        self.blocked_count = 0
        self.total_processed = 0
        logger.info("Cleared all cache")

    def get_user_recent_messages(self, user_id: int, limit: int = 5) -> list:
        """
        Возвращает последние сообщения пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество сообщений
            
        Returns:
            list: Список последних сообщений
        """
        if user_id not in self.user_messages:
            return []
        
        user_deque = self.user_messages[user_id]
        return list(user_deque)[-limit:]

# Глобальный экземпляр фильтра
duplicate_filter = DuplicateMessageFilter(
    time_window=300,  # 5 минут
    max_messages_per_user=10,
    similarity_threshold=0.8
)

def is_duplicate_message(user_id: int, message_text: str) -> bool:
    """
    Проверяет, является ли сообщение дубликатом (удобная функция)
    
    Args:
        user_id: ID пользователя
        message_text: Текст сообщения
        
    Returns:
        bool: True если сообщение является дубликатом
    """
    return duplicate_filter.is_duplicate(user_id, message_text)

def get_duplicate_stats() -> Dict[str, int]:
    """
    Возвращает статистику фильтра дубликатов
    
    Returns:
        Dict[str, int]: Статистика
    """
    return duplicate_filter.get_stats()

def clear_user_duplicates(user_id: int) -> None:
    """
    Очищает дубликаты для пользователя
    
    Args:
        user_id: ID пользователя
    """
    duplicate_filter.clear_user_cache(user_id)



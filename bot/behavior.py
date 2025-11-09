"""
Human Behavior Simulator
Максимально реалистичная имитация живого общения в чате
"""

import asyncio
import random
import re
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MessageType(Enum):
    QUESTION = "question"
    STATEMENT = "statement"
    THANKS = "thanks"
    GREETING = "greeting"
    COMPLAINT = "complaint"
    REQUEST = "request"
    CLARIFICATION = "clarification"

class EmotionalState(Enum):
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    THINKING = "thinking"
    HELPFUL = "helpful"
    EMPATHETIC = "empathetic"
    EXCITED = "excited"
    CONCERNED = "concerned"

@dataclass
class HumanBehaviorConfig:
    # Типирование
    min_typing_speed: float = 0.8  # символов в секунду (медленно)
    max_typing_speed: float = 2.5  # символов в секунду (быстро)
    thinking_pause_min: float = 1.0
    thinking_pause_max: float = 4.0
    correction_pause: float = 2.0  # пауза при "исправлении"
    
    # Эмоции и реакции
    emoji_probability: float = 0.3  # Уменьшаем частоту эмодзи
    micro_reaction_probability: float = 0.3  # Уменьшаем микро-реакции
    emotional_response_probability: float = 0.2  # Уменьшаем эмоциональные отклики
    
    # Разбивка сообщений
    max_message_length: int = 200  # Увеличиваем длину сообщений
    split_probability: float = 0.3  # Уменьшаем вероятность разбивки
    connector_probability: float = 0.2  # Уменьшаем связующие фразы
    
    # Человеческие особенности
    typo_probability: float = 0.05  # 5% шанс опечатки
    self_correction_probability: float = 0.3  # 30% шанс самокоррекции
    hesitation_probability: float = 0.2  # 20% шанс колебания

class HumanBehaviorSimulator:
    def __init__(self, config: HumanBehaviorConfig = None):
        self.config = config or HumanBehaviorConfig()
        self.conversation_history = []
        self.user_emotional_context = {}
        self.last_response_time = 0
        
        # Словари для реалистичных реакций
        self._init_reaction_dictionaries()
        
    def _init_reaction_dictionaries(self):
        """Инициализация словарей для реалистичных реакций"""
        
        # Микро-реакции по контексту
        self.micro_reactions = {
            MessageType.QUESTION: [
                "Хм 🤔", "Интересно 💭", "Хороший вопрос! 👍", 
                "Сейчас подумаю... 🧠", "Ага, понял 📝"
            ],
            MessageType.THANKS: [
                "Пожалуйста! 😊", "Рад помочь! ✨", "Всегда пожалуйста! 👍",
                "Не за что! 😄", "Обращайтесь! 🤝"
            ],
            MessageType.REQUEST: [
                "Конечно! 💪", "Помогу! 🤝", "Сейчас разберусь! 🔍",
                "Без проблем! ✅", "Давайте разберемся! 🎯"
            ],
            MessageType.GREETING: [
                "Привет! 👋", "Здравствуйте! 😊", "Рад видеть! ✨",
                "Добро пожаловать! 🌟", "Привет-привет! 😄"
            ],
            MessageType.COMPLAINT: [
                "Понимаю 😔", "Сочувствую 💙", "Давайте решим! 💪",
                "Разберемся! 🔧", "Поможем! 🤝"
            ]
        }
        
        # Эмоциональные смягчители
        self.softeners = [
            "наверное", "кажется", "по ощущениям", "возможно", 
            "скорее всего", "вроде бы", "как мне кажется", "думаю",
            "на мой взгляд", "если честно", "честно говоря"
        ]
        
        # Связующие фразы для естественной разбивки
        self.connectors = [
            "Кстати,", "Также,", "Еще момент:", "Дополню:",
            "И еще:", "Продолжаю:", "Добавлю:", "Важно:",
            "Между прочим,", "Кроме того,", "Плюс к этому,"
        ]
        
        # Эмодзи по эмоциональному состоянию
        self.emojis_by_emotion = {
            EmotionalState.POSITIVE: ["😊", "😄", "✨", "🌟", "👍", "👌", "🎉"],
            EmotionalState.THINKING: ["🤔", "💭", "🧠", "🤓", "📚", "🔍"],
            EmotionalState.HELPFUL: ["🤝", "💪", "✅", "🎯", "📋", "🔧"],
            EmotionalState.EMPATHETIC: ["💙", "🤗", "😌", "💚", "🌸"],
            EmotionalState.EXCITED: ["🚀", "⚡", "🔥", "💥", "🎊"],
            EmotionalState.CONCERNED: ["😟", "😔", "🤔", "💭", "🔍"],
            EmotionalState.NEUTRAL: ["📝", "📌", "🔍", "⚙️", "📋"]
        }
        
        # Паттерны колебаний и размышлений
        self.hesitation_patterns = [
            "эээ...", "ммм...", "хм...", "ну...", "как бы...",
            "в общем...", "то есть...", "в принципе..."
        ]
        
        # Паттерны самокоррекции
        self.correction_patterns = [
            "точнее", "вернее", "лучше сказать", "имею в виду",
            "то есть", "а именно", "конкретно"
        ]

    def analyze_message_context(self, text: str, user_id: str) -> Tuple[MessageType, EmotionalState]:
        """Анализ контекста сообщения для определения типа и эмоционального состояния"""
        
        text_lower = text.lower()
        
        # Определяем тип сообщения
        if text.strip().endswith('?'):
            message_type = MessageType.QUESTION
        elif any(word in text_lower for word in ["спасибо", "благодарю", "спасибо большое"]):
            message_type = MessageType.THANKS
        elif any(word in text_lower for word in ["привет", "здравствуйте", "добро пожаловать"]):
            message_type = MessageType.GREETING
        elif any(word in text_lower for word in ["проблема", "ошибка", "не работает", "плохо"]):
            message_type = MessageType.COMPLAINT
        elif any(word in text_lower for word in ["помогите", "помощь", "поддержка", "нужно"]):
            message_type = MessageType.REQUEST
        else:
            message_type = MessageType.STATEMENT
        
        # Определяем эмоциональное состояние
        if any(word in text_lower for word in ["отлично", "супер", "классно", "здорово"]):
            emotional_state = EmotionalState.POSITIVE
        elif any(word in text_lower for word in ["думаю", "кажется", "возможно", "наверное"]):
            emotional_state = EmotionalState.THINKING
        elif any(word in text_lower for word in ["помогу", "поддержка", "решение"]):
            emotional_state = EmotionalState.HELPFUL
        elif any(word in text_lower for word in ["понимаю", "сочувствую", "жаль"]):
            emotional_state = EmotionalState.EMPATHETIC
        elif any(word in text_lower for word in ["ура", "круто", "вау", "потрясающе"]):
            emotional_state = EmotionalState.EXCITED
        elif any(word in text_lower for word in ["проблема", "беспокоит", "волнует"]):
            emotional_state = EmotionalState.CONCERNED
        else:
            emotional_state = EmotionalState.NEUTRAL
            
        return message_type, emotional_state

    def calculate_realistic_typing_time(self, text: str) -> float:
        """Расчет реалистичного времени печати с учетом человеческих особенностей"""
        
        # Базовое время печати
        base_time = len(text) / random.uniform(self.config.min_typing_speed, self.config.max_typing_speed)
        
        # Добавляем паузы на размышления
        thinking_pauses = 0
        sentences = text.split('.')
        for sentence in sentences:
            if len(sentence.strip()) > 20:  # Длинные предложения требуют размышлений
                thinking_pauses += random.uniform(0.5, 2.0)
        
        # Добавляем паузы на исправления (если есть опечатки)
        if random.random() < self.config.typo_probability:
            base_time += self.config.correction_pause
        
        # Добавляем колебания
        if random.random() < self.config.hesitation_probability:
            base_time += random.uniform(1.0, 3.0)
        
        return base_time + thinking_pauses

    def add_human_imperfections(self, text: str) -> str:
        """Добавление человеческих несовершенств в текст"""
        
        # Добавляем опечатки (редко)
        if random.random() < self.config.typo_probability:
            words = text.split()
            if words:
                typo_word_index = random.randint(0, len(words) - 1)
                word = words[typo_word_index]
                if len(word) > 3:
                    # Простая опечатка - замена одной буквы
                    char_index = random.randint(1, len(word) - 2)
                    typo_word = word[:char_index] + random.choice('абвгдеёжзийклмнопрстуфхцчшщъыьэюя') + word[char_index + 1:]
                    words[typo_word_index] = typo_word
                    text = ' '.join(words)
        
        # Добавляем самокоррекцию
        if random.random() < self.config.self_correction_probability and len(text) > 50:
            correction = random.choice(self.correction_patterns)
            # Вставляем коррекцию в середину предложения
            sentences = text.split('.')
            if len(sentences) > 1:
                mid_sentence = len(sentences) // 2
                sentences[mid_sentence] = f"{sentences[mid_sentence]}, {correction},"
                text = '. '.join(sentences)
        
        # Добавляем колебания
        if random.random() < self.config.hesitation_probability:
            hesitation = random.choice(self.hesitation_patterns)
            # Вставляем в начало или середину
            if random.random() < 0.5:
                text = f"{hesitation} {text}"
            else:
                words = text.split()
                if len(words) > 3:
                    insert_pos = len(words) // 2
                    words.insert(insert_pos, hesitation)
                    text = ' '.join(words)
        
        return text

    def add_emotional_response(self, text: str, message_type: MessageType, emotional_state: EmotionalState) -> str:
        """Добавление эмоционального отклика"""
        
        # Добавляем микро-реакцию только для определенных типов сообщений
        if (message_type in [MessageType.QUESTION, MessageType.REQUEST, MessageType.COMPLAINT] and 
            random.random() < self.config.micro_reaction_probability):
            if message_type in self.micro_reactions:
                reaction = random.choice(self.micro_reactions[message_type])
                text = f"{reaction}\n\n{text}"
        
        # Добавляем смягчитель реже и только для длинных ответов
        if (len(text) > 100 and 
            random.random() < 0.2 and 
            message_type not in [MessageType.THANKS, MessageType.GREETING]):
            softener = random.choice(self.softeners)
            # Добавляем в начало первого предложения
            sentences = text.split('.')
            if sentences and sentences[0].strip():
                first_sentence = sentences[0].strip()
                if not first_sentence.lower().startswith(tuple(s.lower() for s in self.softeners)):
                    sentences[0] = f"{softener}, {first_sentence.lower()}"
                    text = '. '.join(sentences)
        
        # Добавляем эмодзи реже и только в конце
        if random.random() < self.config.emoji_probability:
            if emotional_state in self.emojis_by_emotion:
                emoji = random.choice(self.emojis_by_emotion[emotional_state])
                text += f" {emoji}"
        
        return text

    def split_message_naturally(self, text: str) -> List[str]:
        """Естественная разбивка сообщения на части"""
        
        # Если сообщение короткое - не разбиваем
        if len(text) <= self.config.max_message_length:
            return [text]
        
        # Проверяем, стоит ли разбивать
        if random.random() > self.config.split_probability:
            return [text]
        
        # Разбиваем по предложениям
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            return [text]
        
        # Группируем предложения в сообщения (более логично)
        messages = []
        current_message = ""
        
        for sentence in sentences:
            # Разбиваем только по очень длинным блокам или ключевым словам
            if (len(current_message + sentence) > self.config.max_message_length * 1.5 and current_message) or \
               (any(word in sentence.lower() for word in ["важно", "обратите внимание", "кстати", "между прочим"]) and current_message):
                messages.append(current_message.strip())
                current_message = sentence + "."
            else:
                current_message += sentence + ". "
        
        if current_message.strip():
            messages.append(current_message.strip())
        
        # Если получилось слишком много сообщений - объединяем
        if len(messages) > 3:
            # Объединяем в 2-3 сообщения
            combined_messages = []
            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    combined = messages[i] + " " + messages[i + 1]
                    combined_messages.append(combined)
                else:
                    combined_messages.append(messages[i])
            messages = combined_messages
        
        # Добавляем связующие фразы редко
        if len(messages) > 1:
            for i in range(1, len(messages)):
                if random.random() < self.config.connector_probability:
                    connector = random.choice(self.connectors)
                    messages[i] = f"{connector} {messages[i].lower()}"
        
        return messages

    def process_response(self, text: str, user_id: str) -> Tuple[List[str], float]:
        """Основная функция обработки ответа для максимально реалистичного поведения"""
        
        # Анализируем контекст
        message_type, emotional_state = self.analyze_message_context(text, user_id)
        
        # Добавляем человеческие несовершенства
        text = self.add_human_imperfections(text)
        
        # Добавляем эмоциональный отклик
        text = self.add_emotional_response(text, message_type, emotional_state)
        
        # Разбиваем на сообщения
        messages = self.split_message_naturally(text)
        
        # Рассчитываем время печати для каждого сообщения
        typing_times = []
        for message in messages:
            typing_time = self.calculate_realistic_typing_time(message)
            typing_times.append(typing_time)
        
        # Сохраняем контекст для будущих ответов
        self.conversation_history.append({
            'user_id': user_id,
            'message_type': message_type,
            'emotional_state': emotional_state,
            'timestamp': time.time()
        })
        
        # Ограничиваем историю
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return messages, typing_times

    def get_thinking_delay(self, user_id: str) -> float:
        """Получение задержки на размышления в зависимости от контекста"""
        
        # Базовая задержка
        base_delay = random.uniform(self.config.thinking_pause_min, self.config.thinking_pause_max)
        
        # Увеличиваем задержку для сложных вопросов
        recent_messages = [msg for msg in self.conversation_history if msg['user_id'] == user_id][-3:]
        if recent_messages:
            last_message = recent_messages[-1]
            if last_message['message_type'] == MessageType.QUESTION:
                base_delay += random.uniform(1.0, 3.0)
            elif last_message['message_type'] == MessageType.COMPLAINT:
                base_delay += random.uniform(0.5, 2.0)
        
        return base_delay

    def get_message_delay(self, message_index: int, total_messages: int) -> float:
        """Получение задержки между сообщениями"""
        
        if message_index >= total_messages - 1:
            return 0  # Последнее сообщение
        
        # Базовая задержка
        base_delay = random.uniform(1.0, 3.0)
        
        # Увеличиваем задержку для длинных сообщений
        if total_messages > 2:
            base_delay += random.uniform(0.5, 2.0)
        
        return base_delay



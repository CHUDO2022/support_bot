# -*- coding: utf-8 -*-

import asyncio
import json
import os
import logging
import random
from typing import Dict, Optional
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from openai import AsyncOpenAI
from human_behavior import HumanBehaviorSimulator, HumanBehaviorConfig
# Убрали калькулятор - работаем только с OpenAI API
from file_manager import FileManager
from smart_file_detector import SmartFileDetector
from text_cleaner import clean_source_marks
from duplicate_filter import is_duplicate_message, get_duplicate_stats, clear_user_duplicates

# Load environment variables
# load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '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')
ASSISTANT_ID = os.getenv('ASSISTANT_ID', 'asst_OKyZ877MdAv0nRKyeuuXuod2')
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', '22432346'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '853825756299c7ae3527975e76ccb59e')

BOT_NAME = os.getenv('BOT_NAME', 'support_bot_v4')
THREADS_FILE = 'threads.json'
BOT_STATE_FILE = 'bot_state.json'
LOG_LEVEL = logging.INFO

HUMAN_BEHAVIOR_ENABLED = True
HUMAN_BEHAVIOR_CONFIG = HumanBehaviorConfig(
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

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

openai_client: Optional[AsyncOpenAI] = None
app: Optional[Client] = None
user_threads: Dict[str, str] = {}
processing_users = set()  # Track users currently being processed

human_simulator = HumanBehaviorSimulator(HUMAN_BEHAVIOR_CONFIG)
file_manager = FileManager()  # Инициализируем менеджер файлов
smart_detector = None  # Будет инициализирован после создания OpenAI клиента

bot_state = {
    "global_enabled": True,
    "blacklisted_chats": {
        "by_id": [],
        "by_username": [],
        "by_title": []
    },
    "admin_users": []
}

def load_threads() -> Dict[str, str]:
    """Load user threads from JSON file."""
    if os.path.exists(THREADS_FILE):
        try:
            with open(THREADS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} threads from {THREADS_FILE}")
                return data
        except Exception as e:
            logger.error(f"Error loading threads: {e}")
            return {}
    return {}

def save_threads() -> None:
    """Save user threads to JSON file."""
    try:
        with open(THREADS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_threads, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(user_threads)} threads to {THREADS_FILE}")
    except Exception as e:
        logger.error(f"Error saving threads: {e}")

def load_bot_state() -> None:
    """Load bot state from JSON file."""
    global bot_state
    try:
        if os.path.exists(BOT_STATE_FILE):
            with open(BOT_STATE_FILE, 'r', encoding='utf-8') as f:
                loaded_state = json.load(f)
                
                if "blacklisted_chats" in loaded_state:
                    if isinstance(loaded_state["blacklisted_chats"], list):
                        logger.info("Migrating old blacklist format to new format")
                        old_blacklist = loaded_state["blacklisted_chats"]
                        loaded_state["blacklisted_chats"] = {
                            "by_id": old_blacklist,
                            "by_username": [],
                            "by_title": []
                        }
                        with open(BOT_STATE_FILE, 'w', encoding='utf-8') as f:
                            json.dump(loaded_state, f, ensure_ascii=False, indent=2)
                        logger.info("Migration completed and saved")
                
                bot_state.update(loaded_state)
                logger.info(f"Loaded bot state from {BOT_STATE_FILE}")
    except Exception as e:
        logger.error(f"Error loading bot state: {e}")

def save_bot_state() -> None:
    """Save bot state to JSON file."""
    try:
        with open(BOT_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(bot_state, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved bot state to {BOT_STATE_FILE}")
    except Exception as e:
        logger.error(f"Error saving bot state: {e}")

def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in bot_state["admin_users"] or len(bot_state["admin_users"]) == 0

def is_bot_active_in_chat(chat_id: int, chat_username: str = None, chat_title: str = None) -> bool:
    """Check if bot is active in specific chat."""
    if not bot_state["global_enabled"]:
        return False
    
    if not isinstance(bot_state["blacklisted_chats"], dict):
        logger.warning("Invalid blacklisted_chats structure, resetting to default")
        bot_state["blacklisted_chats"] = {"by_id": [], "by_username": [], "by_title": []}
        save_bot_state()
    
    if "by_id" in bot_state["blacklisted_chats"] and chat_id in bot_state["blacklisted_chats"]["by_id"]:
        return False
    
    if (chat_username and "by_username" in bot_state["blacklisted_chats"] and 
        chat_username in bot_state["blacklisted_chats"]["by_username"]):
        return False
    
    if (chat_title and "by_title" in bot_state["blacklisted_chats"] and 
        chat_title in bot_state["blacklisted_chats"]["by_title"]):
        return False
    
    return True

def get_chat_info(message) -> tuple:
    """Extract chat information from message."""
    chat_id = message.chat.id
    chat_username = getattr(message.chat, 'username', None)
    chat_title = getattr(message.chat, 'title', None)
    return chat_id, chat_username, chat_title

async def human_like_typing(client: Client, chat_id: int, message_length: int = 100) -> None:
    """Show typing indicator briefly (no delays)."""
    await client.send_chat_action(chat_id, ChatAction.TYPING)
    await asyncio.sleep(0.5)

async def send_message_human_like(client: Client, chat_id: int, text: str) -> None:
    """Send message with only typing indicator (no delays)."""
    await client.send_chat_action(chat_id, ChatAction.TYPING)
    await asyncio.sleep(0.5)
    
    await client.send_chat_action(chat_id, ChatAction.CANCEL)
    
    await client.send_message(chat_id, text)

async def send_human_like_response(client: Client, chat_id: int, text: str, user_id: str) -> None:
    """Send response with only typing indicator (no delays)."""
    await client.send_chat_action(chat_id, ChatAction.TYPING)
    await asyncio.sleep(0.5)
    
    await client.send_chat_action(chat_id, ChatAction.CANCEL)
    
    try:
        await client.send_message(chat_id, text)
        logger.info("Sent message")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

async def quick_typing(client: Client, chat_id: int, duration: float = None) -> None:
    """Quick typing for simple commands."""
    await client.send_chat_action(chat_id, ChatAction.TYPING)
    await asyncio.sleep(0.3)

async def get_or_create_thread(user_id: str) -> str:
    """Get existing thread or create new one for user."""
    if user_id not in user_threads:
        try:
            thread = await openai_client.beta.threads.create()
            user_threads[user_id] = thread.id
            save_threads()
            logger.info(f"Created new thread for user {user_id}: {thread.id}")
        except Exception as e:
            logger.error(f"Error creating thread for user {user_id}: {e}")
            raise
    return user_threads[user_id]

async def get_assistant_response(user_id: str, message_text: str) -> str:
    """Get response from OpenAI Assistant with proper thread management."""
    try:
        thread_id = await get_or_create_thread(user_id)
        
        try:
            runs = await openai_client.beta.threads.runs.list(thread_id=thread_id, limit=1)
            if runs.data and runs.data[0].status in ['queued', 'in_progress', 'requires_action']:
                logger.info(f"Waiting for active run to complete for user {user_id}")
                active_run = runs.data[0]
                
                timeout = 30
                elapsed = 0
                while active_run.status in ['queued', 'in_progress', 'requires_action'] and elapsed < timeout:
                    await asyncio.sleep(1)
                    elapsed += 1
                    active_run = await openai_client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=active_run.id
                    )
                
                if elapsed >= timeout:
                    logger.warning(f"Timeout waiting for active run for user {user_id}")
                    try:
                        await openai_client.beta.threads.runs.cancel(
                            thread_id=thread_id,
                            run_id=active_run.id
                        )
                    except:
                        pass
        except Exception as e:
            logger.warning(f"Error checking active runs: {e}")
        
        # Add user message to thread with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await openai_client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=message_text
                )
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed to add message: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # Wait before retry
                else:
                    raise e
        
        # Run assistant
        run = await openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        # Wait for completion with timeout
        timeout = 60  # 60 seconds timeout
        elapsed = 0
        while run.status in ['queued', 'in_progress', 'requires_action'] and elapsed < timeout:
            await asyncio.sleep(1)
            elapsed += 1
            run = await openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        if run.status == 'completed':
            messages = await openai_client.beta.threads.messages.list(thread_id=thread_id)
            if messages.data:
                last_message = messages.data[0]
                if last_message.content:
                    response_text = last_message.content[0].text.value
                    # Очищаем ответ от меток source
                    cleaned_response = clean_source_marks(response_text)
                    return cleaned_response
        
        logger.error(f"Run failed with status: {run.status} (timeout: {elapsed >= timeout})")
        return f"Ошибка ассистента: {run.status}"
            
    except Exception as e:
        logger.error(f"Error getting assistant response: {e}")
        return f"Ошибка: {str(e)}"

async def detect_request_type_smart(message_text: str) -> Dict[str, any]:
    """Умное определение типа запроса с использованием OpenAI"""
    try:
        if smart_detector:
            result = await smart_detector.detect_request_type(message_text)
            
            # Минимальная валидация - только очень низкая уверенность
            if result["confidence"] < 0.5:
                logger.info(f"Very low confidence ({result['confidence']}) for {result['type']}, treating as GENERAL_CHAT")
                return {"type": "GENERAL_CHAT", "confidence": 0.9, "reasoning": "very low confidence in request"}
            
            return result
        else:
            # Fallback к простому определению
            return {"type": "GENERAL_CHAT", "confidence": 0.5, "reasoning": "smart detector not available"}
    except Exception as e:
        logger.error(f"Error in smart detection: {e}")
        return {"type": "GENERAL_CHAT", "confidence": 0.5, "reasoning": f"error: {str(e)}"}

# Убрали функцию расчетов - работаем только с OpenAI API

async def handle_tz_file_request(client: Client, message) -> None:
    """Обрабатывает запросы на файл ТЗ"""
    try:
        # Проверяем, не отправляли ли уже файл недавно
        user_id = str(message.from_user.id)
        current_time = asyncio.get_event_loop().time()
        
        # Простая проверка на спам (если файл отправлялся в последние 30 секунд)
        if hasattr(handle_tz_file_request, 'last_sent') and hasattr(handle_tz_file_request, 'last_user'):
            if (handle_tz_file_request.last_user == user_id and 
                current_time - handle_tz_file_request.last_sent < 30):
                # Отвечаем контекстно вместо повторной отправки файла
                await send_human_like_response(
                    client, 
                    message.chat.id, 
                    "Файл ТЗ уже отправлен выше! Если нужна помощь с заполнением - спрашивайте 🤝", 
                    user_id
                )
                return
        
        # Обновляем время последней отправки
        handle_tz_file_request.last_sent = current_time
        handle_tz_file_request.last_user = user_id
        
        # Сначала отправляем естественный ответ
        await send_human_like_response(
            client, 
            message.chat.id, 
            "Понял! Сейчас отправлю файл ТЗ для заполнения 🙂", 
            user_id
        )
        
        # Затем отправляем файл
        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
        await file_manager.send_tz_file(client, message.chat.id)
        logger.info(f"Sent TZ file to user {user_id}")
    except Exception as e:
        logger.error(f"Error handling TZ file request: {e}")
        await send_human_like_response(
            client, 
            message.chat.id, 
            f"Извините, возникла проблема с отправкой файла. Попробуйте позже 🤝", 
            str(message.from_user.id)
        )

async def handle_warehouse_request_with_chatgpt(client: Client, message) -> None:
    """Обрабатывает запросы о складе с интеграцией ChatGPT и изображений"""
    try:
        # Проверяем, упоминается ли Казань в запросе
        text_lower = message.text.lower()
        kazan_keywords = ["казань", "казани", "казан", "в казани", "в казань"]
        
        if any(keyword in text_lower for keyword in kazan_keywords):
            # Для Казани - отправляем изображения с красивой подписью
            await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
            
            # Красивая подпись с адресом и ссылкой
            caption = (
                "📍 **Адрес склада в Казани:**\n"
                "ул. Горьковское Шоссе, 49 (Технополис \"Химград\")\n\n"
                "🗺️ **Ссылка на карту:**\n"
                "https://yandex.ru/maps/-/CHX8J03h\n\n"
                "📸 **Фото склада и схема проезда** 👆"
            )
            
            await file_manager.send_warehouse_with_caption(client, message.chat.id, caption)
            
            logger.info(f"Sent warehouse info for Kazan to user {message.from_user.id}")
        else:
            # Для других городов - только ответ от ChatGPT
            response = await get_assistant_response(str(message.from_user.id), message.text)
            await send_human_like_response(client, message.chat.id, response, str(message.from_user.id))
            logger.info(f"Sent ChatGPT response for non-Kazan request to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error handling warehouse request with ChatGPT: {e}")
        await send_human_like_response(
            client, 
            message.chat.id, 
            f"Извините, возникла проблема с обработкой запроса. Попробуйте позже 🤝", 
            str(message.from_user.id)
        )

async def handle_warehouse_images_request(client: Client, message) -> None:
    """Обрабатывает запросы на изображения склада (старая функция для совместимости)"""
    try:
        # Сначала отправляем естественный ответ
        await send_human_like_response(
            client, 
            message.chat.id, 
            "Конечно! Сейчас отправлю информацию о складе и схему проезда 👌", 
            str(message.from_user.id)
        )
        
        # Затем отправляем файлы
        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
        await file_manager.send_warehouse_images(client, message.chat.id)
        logger.info(f"Sent warehouse images to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error handling warehouse images request: {e}")
        await send_human_like_response(
            client, 
            message.chat.id, 
            f"Извините, возникла проблема с отправкой файлов. Попробуйте позже 🤝", 
            str(message.from_user.id)
        )

async def handle_private_message(client: Client, message) -> None:
    """Handle private messages."""
    if not message.text:
        return
    
    # For private messages, check if the user is blocked
    user_id = message.from_user.id
    user_username = getattr(message.from_user, 'username', None)
    
    # Check if bot is active globally
    if not bot_state["global_enabled"]:
        return
    
    # Check if user is blocked by ID
    if user_id in bot_state["blacklisted_chats"]["by_id"]:
        logger.info(f"User {user_id} is blocked by ID")
        return
    
    # Check if user is blocked by username
    if user_username and f"@{user_username}" in bot_state["blacklisted_chats"]["by_username"]:
        logger.info(f"User @{user_username} is blocked by username")
        return
    
    # Check if user is already being processed
    if user_id in processing_users:
        logger.info(f"User {user_id} is already being processed, skipping")
        return
    
    # Add user to processing set
    processing_users.add(user_id)
    
    # Debug info
    logger.info(f"Processing message from user {user_id} (@{user_username}) - not blocked")
    
    # Проверяем на дубликаты сообщений
    if is_duplicate_message(user_id, message.text):
        logger.info(f"Duplicate message blocked from user {user_id}: {message.text[:50]}...")
        return
    
    try:
        # Умное определение типа запроса
        detection_result = await detect_request_type_smart(message.text)
        request_type = detection_result.get("type", "GENERAL_CHAT")
        confidence = detection_result.get("confidence", 0.5)
        
        logger.info(f"Detected request type: {request_type} (confidence: {confidence})")
        
        # Обрабатываем в зависимости от типа
        if request_type == "TZ_FILE":
            await handle_tz_file_request(client, message)
        elif request_type == "WAREHOUSE_IMAGES":
            # Для запросов о складе - сначала получаем ответ от ChatGPT, затем добавляем изображения
            await handle_warehouse_request_with_chatgpt(client, message)
        else:  # GENERAL_CHAT и LOGISTICS_CALCULATION - обрабатываем как обычное общение
            # Обычная обработка через OpenAI Assistant
            response = await get_assistant_response(str(message.from_user.id), message.text)
            await send_human_like_response(client, message.chat.id, response, str(message.from_user.id))
            logger.info(f"Replied to private message from user {message.from_user.id}")
            
    except Exception as e:
        logger.error(f"Error handling private message: {e}")
    finally:
        # Remove user from processing set
        processing_users.discard(user_id)

async def handle_group_message(client: Client, message) -> None:
    """Handle group messages when bot is mentioned."""
    if not message.mentioned or not message.text:
        return
    
    # Check if bot is active in this chat
    chat_id, chat_username, chat_title = get_chat_info(message)
    if not is_bot_active_in_chat(chat_id, chat_username, chat_title):
        return
    
    user_text = message.text.replace(f'@{BOT_NAME}', '').strip()
    if not user_text:
        return
    
    try:
        # Умное определение типа запроса
        detection_result = await detect_request_type_smart(user_text)
        request_type = detection_result.get("type", "GENERAL_CHAT")
        confidence = detection_result.get("confidence", 0.5)
        
        logger.info(f"Detected group request type: {request_type} (confidence: {confidence})")
        
        # Обрабатываем в зависимости от типа
        if request_type == "TZ_FILE":
            await handle_tz_file_request(client, message)
        elif request_type == "WAREHOUSE_IMAGES":
            # Для запросов о складе - сначала получаем ответ от ChatGPT, затем добавляем изображения
            await handle_warehouse_request_with_chatgpt(client, message)
        else:  # GENERAL_CHAT и LOGISTICS_CALCULATION - обрабатываем как обычное общение
            # Обычная обработка через OpenAI Assistant
            response = await get_assistant_response(str(message.from_user.id), user_text)
            await send_human_like_response(client, message.chat.id, response, str(message.from_user.id))
            logger.info(f"Replied to group message from user {message.from_user.id}")
            
    except Exception as e:
        logger.error(f"Error handling group message: {e}")

# Остальные функции остаются без изменений...
async def start_command(client: Client, message) -> None:
    """Handle /start command."""
    await quick_typing(client, message.chat.id)
    await message.reply(f'🚀 {BOT_NAME} запущен! Отправьте сообщение для общения.\n\n💡 **Доступные функции:**\n• Расчет логистических услуг\n• Отправка файла ТЗ\n• Изображения склада\n• Обычное общение\n\n🤖 **Умное определение запросов** - бот сам поймет, что вам нужно!')

async def clear_context(client: Client, message) -> None:
    """Handle /clear command."""
    user_id = str(message.from_user.id)
    if user_id in user_threads:
        del user_threads[user_id]
        save_threads()
        logger.info(f"Cleared context for user {user_id}")
    await quick_typing(client, message.chat.id)
    await message.reply('✅ Контекст очищен!')

async def clear_duplicates_command(client: Client, message) -> None:
    """Handle /clear_duplicates command."""
    user_id = message.from_user.id
    clear_user_duplicates(user_id)
    logger.info(f"Cleared duplicates for user {user_id}")
    await quick_typing(client, message.chat.id)
    await message.reply('🔄 Кэш дубликатов очищен!')

async def status_command(client: Client, message) -> None:
    """Handle /status command."""
    user_id = str(message.from_user.id)
    thread_id = user_threads.get(user_id, "Нет")
    total_threads = len(user_threads)
    global_status = "🟢 Включен" if bot_state["global_enabled"] else "🔴 Выключен"
    
    # Count blocked chats
    total_blocked = (len(bot_state["blacklisted_chats"]["by_id"]) + 
                    len(bot_state["blacklisted_chats"]["by_username"]) + 
                    len(bot_state["blacklisted_chats"]["by_title"]))
    
    # Получаем статистику дубликатов
    duplicate_stats = get_duplicate_stats()
    
    status_text = (
        f'📊 **Статус бота:** {global_status}\n'
        f'🧵 **Thread:** {thread_id}\n'
        f'🤖 **Ассистент:** {BOT_NAME}\n'
        f'📁 **Всего threads:** {total_threads}\n'
        f'🚫 **Заблокированных чатов:** {total_blocked}\n'
        f'   • По ID: {len(bot_state["blacklisted_chats"]["by_id"])}\n'
        f'   • По username: {len(bot_state["blacklisted_chats"]["by_username"])}\n'
        f'   • По названию: {len(bot_state["blacklisted_chats"]["by_title"])}\n'
        f'💰 **Калькулятор логистики:** 🟢 Активен\n'
        f'📁 **Файлы:** 🟢 Доступны\n'
        f'🧠 **Умное определение:** 🟢 Активно\n'
        f'🔄 **Фильтр дубликатов:** 🟢 Активен\n'
        f'   • Обработано: {duplicate_stats["total_processed"]}\n'
        f'   • Заблокировано: {duplicate_stats["blocked_count"]}\n'
        f'   • Активных пользователей: {duplicate_stats["active_users"]}'
    )
    
    await quick_typing(client, message.chat.id)
    await message.reply(status_text)

async def help_command(client: Client, message) -> None:
    """Show help information."""
    help_text = f"""
🤖 **Support Bot v4 - Умный бот с ИИ**

**Основные команды:**
/start - Запуск бота
/clear - Очистить контекст диалога
/clear_duplicates - Очистить кэш дубликатов
/status - Показать статус бота
/help - Показать эту справку

**🧠 Умное определение запросов:**
Бот использует ИИ для понимания ваших запросов:

**💰 Расчет логистики:**
• "носки 1000 штук, вес 100 грамм, ozon, москва"
• "сколько стоит доставка футболок 500 шт"
• "расчет для кроссовок 100 штук, 800г, яндекс"

**📋 Файл ТЗ:**
• "мне нужен файл ТЗ"
• "пришлите техническое задание"
• "эксель файл для заполнения"
• "бланк для расчета"

**🏢 Изображения склада:**
• "покажите склад"
• "как добраться до вас"
• "схема проезда"
• "фото склада"
• "адрес склада"

**💬 Обычное общение:**
• "привет"
• "как дела"
• "помогите"
• "что умеет бот"

**Поддерживаемые товары:**
🧦 Носки, 👕 Одежда, 👟 Обувь, 👜 Аксессуары, 👙 Белье, ⚽ Спорт

**Маркетплейсы:**
🏪 Ozon, Wildberries, Яндекс.Маркет, AliExpress, Lamoda, ASOS

**Города:**
🏙️ Москва, СПб, Новосибирск, Екатеринбург, Казань, и другие

**Примечание:** Бот автоматически определит тип запроса и ответит соответствующим образом!
    """
    await quick_typing(client, message.chat.id)
    await message.reply(help_text)

def setup_handlers() -> None:
    """Setup Telegram message handlers."""
    if not app:
        raise RuntimeError("Telegram client not initialized")
    
    # Message handlers
    app.on_message(filters.private & filters.incoming & ~filters.me)(handle_private_message)
    app.on_message(filters.group & filters.incoming & ~filters.me)(handle_group_message)
    
    # Basic command handlers
    app.on_message(filters.command('start') & filters.private)(start_command)
    app.on_message(filters.command('clear') & filters.private)(clear_context)
    app.on_message(filters.command('clear_duplicates') & filters.private)(clear_duplicates_command)
    app.on_message(filters.command('status') & filters.private)(status_command)
    app.on_message(filters.command('help') & filters.private)(help_command)
    
    logger.info("Message handlers setup complete")

def initialize_clients() -> None:
    """Initialize OpenAI and Telegram clients with session management."""
    global openai_client, app, smart_detector
    
    try:
        # Initialize OpenAI client
        logger.info("Initializing OpenAI client...")
        openai_client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            default_headers={"OpenAI-Beta": "assistants=v2"}
        )
        logger.info("OpenAI client initialized successfully")
        
        # Initialize smart detector
        smart_detector = SmartFileDetector(openai_client)
        logger.info("Smart file detector initialized successfully")
        
        # Initialize Telegram client
        logger.info("Initializing Telegram client...")
        app = Client(
            BOT_NAME, 
            api_id=TELEGRAM_API_ID, 
            api_hash=TELEGRAM_API_HASH
        )
        logger.info("Telegram client initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}", exc_info=True)
        raise

def main() -> None:
    """Main function to run the bot."""
    global user_threads
    
    print("🤖 Запуск Support Bot v4 с умным ИИ...")
    print("=" * 60)
    
    try:
        # Load existing threads
        user_threads = load_threads()
        print(f"📁 Загружено {len(user_threads)} threads")
        
        # Load bot state
        load_bot_state()
        print(f"📊 Статус бота: {'🟢 Включен' if bot_state['global_enabled'] else '🔴 Выключен'}")
        
        # Initialize clients
        print("\n🔧 Инициализация клиентов...")
        initialize_clients()
        
        # Setup handlers
        setup_handlers()
        
        # Start bot
        print("\n🚀 Бот запущен!")
        print("💰 Калькулятор логистики активен!")
        print("📁 Файлы и изображения готовы!")
        print("🧠 Умное определение запросов активно!")
        print("=" * 60)
        logger.info(f"🚀 {BOT_NAME} с умным ИИ запущен!")
        
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 Остановка бота...")
        logger.info("Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
Модуль для управления файлами (Excel ТЗ, изображения склада)
"""

import os
import logging
from typing import List, Optional
from pyrogram import Client
from pyrogram.types import InputMediaPhoto, InputMediaVideo

logger = logging.getLogger(__name__)

class FileManager:
    """Класс для управления файлами бота"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        self.images_path = os.path.join(base_path, "Картинки")
        self.tz_file = os.path.join(base_path, "ТЗ.xlsx")
        
        # Проверяем наличие папки с изображениями
        if not os.path.exists(self.images_path):
            os.makedirs(self.images_path)
            logger.warning(f"Создана папка для изображений: {self.images_path}")
    
    def get_tz_file(self) -> Optional[str]:
        """Получает путь к файлу ТЗ"""
        if os.path.exists(self.tz_file):
            return self.tz_file
        else:
            logger.error(f"Файл ТЗ не найден: {self.tz_file}")
            return None
    
    def get_warehouse_images(self) -> List[str]:
        """Получает список изображений склада"""
        images = []
        if os.path.exists(self.images_path):
            for file in os.listdir(self.images_path):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    images.append(os.path.join(self.images_path, file))
        return images
    
    def get_warehouse_videos(self) -> List[str]:
        """Получает список видео склада"""
        videos = []
        if os.path.exists(self.images_path):
            for file in os.listdir(self.images_path):
                if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    videos.append(os.path.join(self.images_path, file))
        return videos
    
    async def send_tz_file(self, client: Client, chat_id: int) -> bool:
        """Отправляет файл ТЗ клиенту"""
        try:
            tz_file_path = self.get_tz_file()
            if not tz_file_path:
                await client.send_message(chat_id, "❌ Файл ТЗ временно недоступен")
                return False
            
            await client.send_document(
                chat_id=chat_id,
                document=tz_file_path,
                caption="📋 **Техническое задание для расчета логистических услуг**\n\n"
                       "Заполните данный файл с параметрами вашего товара и отправьте обратно для получения детального расчета стоимости услуг."
            )
            logger.info(f"Отправлен файл ТЗ в чат {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки файла ТЗ: {e}")
            await client.send_message(chat_id, f"❌ Ошибка отправки файла ТЗ: {str(e)}")
            return False
    
    async def send_warehouse_images(self, client: Client, chat_id: int) -> bool:
        """Отправляет изображения склада клиенту"""
        try:
            images = self.get_warehouse_images()
            videos = self.get_warehouse_videos()
            
            if not images and not videos:
                await client.send_message(chat_id, "📷 Изображения склада временно недоступны")
                return False
            
            # Отправляем изображения
            if images:
                if len(images) == 1:
                    # Одно изображение
                    await client.send_photo(
                        chat_id=chat_id,
                        photo=images[0]
                    )
                else:
                    # Несколько изображений
                    media_group = []
                    for i, img_path in enumerate(images):
                        media_group.append(InputMediaPhoto(media=img_path))
                    
                    await client.send_media_group(chat_id=chat_id, media=media_group)
            
            # Отправляем видео
            if videos:
                for video_path in videos:
                    await client.send_video(
                        chat_id=chat_id,
                        video=video_path
                    )
            
            # Отправляем только краткую информацию об адресах
            await client.send_message(
                chat_id=chat_id,
                text="📍 **Адреса складов:**\n"
                     "• Казань, ул. Беломорская, 69А (фулфилмент)\n"
                     "• Казань, ул. Горьковское Шоссе, 49\n"
                     "https://yandex.ru/maps/-/CHX8J03h"
            )
            
            logger.info(f"Отправлены изображения склада в чат {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки изображений склада: {e}")
            await client.send_message(chat_id, f"❌ Ошибка отправки изображений: {str(e)}")
            return False
    
    async def send_warehouse_images_only(self, client: Client, chat_id: int) -> bool:
        """Отправляет только изображения склада без дополнительного текста"""
        try:
            images = self.get_warehouse_images()
            videos = self.get_warehouse_videos()
            
            if not images and not videos:
                return False
            
            # Отправляем изображения
            if images:
                if len(images) == 1:
                    # Одно изображение
                    await client.send_photo(
                        chat_id=chat_id,
                        photo=images[0]
                    )
                else:
                    # Несколько изображений
                    media_group = []
                    for img_path in images:
                        media_group.append(InputMediaPhoto(media=img_path))
                    
                    await client.send_media_group(chat_id=chat_id, media=media_group)
            
            # Отправляем видео
            if videos:
                for video_path in videos:
                    await client.send_video(
                        chat_id=chat_id,
                        video=video_path
                    )
            
            logger.info(f"Отправлены только изображения склада в чат {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки изображений склада: {e}")
            return False

    async def send_warehouse_with_caption(self, client: Client, chat_id: int, caption: str) -> bool:
        """Отправляет изображения склада с подписью"""
        try:
            images = self.get_warehouse_images()
            videos = self.get_warehouse_videos()
            
            if not images and not videos:
                # Если нет медиа, отправляем только текст
                await client.send_message(chat_id, caption)
                return True
            
            # Отправляем изображения с подписью
            if images:
                if len(images) == 1:
                    # Одно изображение с подписью
                    await client.send_photo(
                        chat_id=chat_id,
                        photo=images[0],
                        caption=caption
                    )
                else:
                    # Несколько изображений - первое с подписью, остальные без
                    media_group = []
                    for i, img_path in enumerate(images):
                        if i == 0:
                            # Первое изображение с подписью
                            media_group.append(InputMediaPhoto(media=img_path, caption=caption))
                        else:
                            # Остальные без подписи
                            media_group.append(InputMediaPhoto(media=img_path))
                    
                    await client.send_media_group(chat_id=chat_id, media=media_group)
            
            # Отправляем видео отдельно
            if videos:
                for video_path in videos:
                    await client.send_video(
                        chat_id=chat_id,
                        video=video_path
                    )
            
            logger.info(f"Отправлены изображения склада с подписью в чат {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки изображений склада с подписью: {e}")
            return False

    async def send_warehouse_info(self, client: Client, chat_id: int) -> bool:
        """Отправляет полную информацию о складе (изображения + ТЗ)"""
        try:
            # Сначала отправляем изображения
            images_sent = await self.send_warehouse_images(client, chat_id)
            
            # Затем отправляем файл ТЗ
            tz_sent = await self.send_tz_file(client, chat_id)
            
            if images_sent or tz_sent:
                await client.send_message(
                    chat_id,
                    "📍 **Дополнительная информация:**\n\n"
                    "• Используйте файл ТЗ для точного расчета\n"
                    "• Изображения помогут найти наш склад\n"
                    "• По всем вопросам обращайтесь к менеджеру"
                )
                return True
            else:
                await client.send_message(chat_id, "❌ Информация о складе временно недоступна")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка отправки информации о складе: {e}")
            await client.send_message(chat_id, f"❌ Ошибка: {str(e)}")
            return False

def test_file_manager():
    """Тестирование FileManager"""
    fm = FileManager()
    
    print("📁 Тестирование FileManager")
    print(f"📋 Файл ТЗ: {fm.get_tz_file()}")
    print(f"🖼️ Изображения: {fm.get_warehouse_images()}")
    print(f"🎥 Видео: {fm.get_warehouse_videos()}")
    
    if fm.get_tz_file():
        print("✅ Файл ТЗ найден")
    else:
        print("❌ Файл ТЗ не найден")
    
    if fm.get_warehouse_images() or fm.get_warehouse_videos():
        print("✅ Медиафайлы склада найдены")
    else:
        print("❌ Медиафайлы склада не найдены")

if __name__ == "__main__":
    test_file_manager()

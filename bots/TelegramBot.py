import os.path
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import telegram
import asyncio
from preprocess.message_preprocess import *


class TelegramBot:
    def __init__(self, token, logger):
        self.bot = telegram.Bot(token=token)
        with open('CONFIG.json', 'r', encoding='utf-8') as f:
            self.CONFIG = json.load(f)
        self.scheduler = AsyncIOScheduler()
        self.logger = logger
        self.active_tasks = set()

        self.sent_posts = {}  # {channel_idx: [links]}
        self._init_sent_posts()

    def _get_sent_posts_filename(self, channel_idx):
        """Генерирует имя файла для хранения отправленных постов канала"""
        channel_url = self.CONFIG["channels"][channel_idx]["url"]
        safe_url = "".join(c for c in channel_url if c.isalnum())
        return f"sent_posts_{safe_url}.json"

    def _init_sent_posts(self):
        """Инициализирует словарь sent_posts для каждого канала"""
        for idx in range(len(self.CONFIG["channels"])):
            filename = self._get_sent_posts_filename(idx)
            self.sent_posts[idx] = self._load_channel_posts(filename)
            self.logger.debug(f"Loaded {len(self.sent_posts[idx])} sent posts for channel {idx}")

    def _load_channel_posts(self, filename):
        """Загружает отправленные посты для конкретного канала"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
            return []
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading sent posts from {filename}: {str(e)}")
            return []

    def _save_channel_posts(self, channel_idx):
        """Сохраняет отправленные посты для конкретного канала"""
        filename = self._get_sent_posts_filename(channel_idx)
        try:
            with open(filename, 'w') as f:
                json.dump(self.sent_posts[channel_idx], f)
        except Exception as e:
            self.logger.error(f"Error saving sent posts to {filename}: {str(e)}")

    async def send_post_to_channel(self, idx):
        """Отправка поста в конкретный канал"""
        try:
            message, image, link = await MessagePreprocess(self.logger, idx).prepare_post()

            if link in self.sent_posts[idx]:
                self.logger.info(f"Канал {idx}: пост {link} уже был отправлен ранее")
                return

            if image:
                await self.bot.send_photo(
                    chat_id=self.CONFIG["channels"][idx]['url'],
                    photo=image,
                    caption=message,
                    parse_mode='MarkdownV2'
                )
            else:
                await self.bot.send_message(
                    chat_id=self.CONFIG["channels"][idx]['url'],
                    text=message,
                    parse_mode='MarkdownV2',
                    disable_web_page_preview=True
                )

            self.sent_posts[idx].append(link)
            self._save_channel_posts(idx)
            self.logger.info(f"Канал {idx}: успешно опубликовано {link}")

        except Exception as e:
            self.logger.error(f"Канал {idx}: ошибка отправки - {str(e)}", exc_info=True)

    def schedule_posts(self):
        """Настройка расписания для каждого канала"""
        for idx, channel in enumerate(self.CONFIG["channels"]):
            if "time" in channel:
                for post_time in channel["time"]:
                    hour, minute = map(int, post_time.split(":"))

                    self.scheduler.add_job(
                        self._wrap_send_task,
                        trigger=CronTrigger(hour=hour, minute=minute),
                        args=[idx],
                        name=f"post_{idx}_{post_time}",
                    )
                    self.logger.info(f"Канал {channel['url']}: пост запланирован на {post_time} UTC")

    async def _wrap_send_task(self, idx):
        """Обёртка для запуска send_post_to_channel в отдельной задаче"""
        task = asyncio.create_task(self.send_post_to_channel(idx))
        self.active_tasks.add(task)
        task.add_done_callback(lambda t: self.active_tasks.discard(t))

    async def run(self):
        self.logger.info("Запуск бота")
        self.schedule_posts()
        self.scheduler.start()

        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.scheduler.shutdown()
            for task in self.active_tasks:
                task.cancel()
            await asyncio.gather(*self.active_tasks, return_exceptions=True)
            self.logger.info("Бот остановлен")
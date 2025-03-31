from apscheduler.schedulers.asyncio import AsyncIOScheduler
import telegram
import asyncio
from preprocess.message_preprocess import *


class TelegramBot:
    def __init__(self, token, sent_posts, logger):
        self.bot = telegram.Bot(token=token) # ЗАМЕНИТЬ НА env
        with open('CONFIG.json', 'r', encoding='utf-8') as f:
            self.CONFIG = json.load(f)
        self.scheduler = AsyncIOScheduler()
        self.sent_posts = sent_posts
        self.sent_links = self.load_sent_posts()
        self.logger = logger
        self.active_tasks = set()

    def load_sent_posts(self):
        try:
            with open(self.sent_posts, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_sent_posts(self):
        with open(self.sent_posts, 'w') as f:
            json.dump(self.sent_links, f)

    async def send_post_to_channel(self, idx):
        """Отправка поста в конкретный канал"""
        try:
            message, image, link = MessagePreprocess(self.logger, idx).prepare_post()
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

            self.sent_links.append(link)
            self.save_sent_posts()
            self.logger.info(f"Канал {self.CONFIG['channels'][idx]['url']}: успешно опубликовано {link}")

            await asyncio.sleep(self.CONFIG['channels'][idx]['interval'])

        except Exception as e:
            self.logger.error(f"Канал {self.CONFIG['channels'][idx]['url']}: ошибка отправки - {str(e)}")

    async def run_channel(self, idx):
        """Бесконечный цикл отправки для одного канала"""
        while True:
            await self.send_post_to_channel(idx)

    async def run_all_channels(self):
        """Запуск всех каналов асинхронно"""
        tasks = []
        for channel_id in range(self.CONFIG["channels"]):
            task = asyncio.create_task(self.run_channel(channel_id))
            self.active_tasks.add(task)
            task.add_done_callback(self.active_tasks.discard)
            tasks.append(task)

        await asyncio.gather(*tasks)


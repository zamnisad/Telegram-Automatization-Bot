from bots.TelegramBot import TelegramBot
from preprocess.set_config import set_config
import logging
import asyncio


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    set_config()
    model = 'ollama3'
    token = '8022820972:AAHUIM55DwEEmSTbm_qEiS1qbw77aS1Kzj8'
    sent = 'sent_posts.json'
    bot = TelegramBot(token, sent, logger)
    logger.info("Запуск RSS-бота с Ollama...")
    asyncio.run(bot.run_all_channels())
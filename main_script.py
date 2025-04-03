from bots.TelegramBot import TelegramBot
from preprocess.set_config import set_config
import logging
import asyncio


async def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    await set_config()
    token = '8022820972:AAHUIM55DwEEmSTbm_qEiS1qbw77aS1Kzj8'
    bot = TelegramBot(token, logger)
    logger.info("Запуск RSS-бота с Ollama...")
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
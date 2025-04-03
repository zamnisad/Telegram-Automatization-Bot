import re
from bots.GenerateBot import *


class MessagePreprocess:
    def __init__(self, logger, idx):
        self.logger = logger
        with open('CONFIG.json', 'r', encoding='utf-8') as f:
            self.CONFIG = json.load(f)
        self.idx = idx
        self.GenerateBot = GenerateBot(logger, idx)

    @staticmethod
    async def escape_markdown_v2(text: str) -> str:
        """
        Экранирует специальные символы для MarkdownV2 в Telegram.
        """
        special_chars = r"_*[]()~`>#+-=|{}.!"
        pattern = r"(?<!<USE>)([{}])".format(re.escape(special_chars)) # TEST

        return re.sub(pattern, r"\\\1", text)

    async def prepare_post(self):
        template, summary, short_sum, image, link, ht_idx = await self.GenerateBot.get_all()
        self.logger.info(f"Обработка информации для {self.CONFIG['channels'][self.idx]['url']}")

        summary = str(await self.escape_markdown_v2(summary))
        template = str(await self.escape_markdown_v2(template))

        hashtags = str(await self.escape_markdown_v2(' '.join(self.CONFIG['channels'][self.idx]['hashtags']))).split()

        fixed_top = f"{template}\n\n"
        ht_idx = list(map(int, ht_idx.split())) # check
        fixed_tail = f"{hashtags[ht_idx[0]]}\n\nПодробнее [тут]({link})"

        for i in ht_idx[1:]:
            fixed_tail = f' {hashtags[int(i)]}' + fixed_tail
        toc_text = f"📑 *Содержание:*\n"

        base_message = f"{fixed_top}{toc_text}\n🔍 {{summary}}\n\n\n" + fixed_tail

        available_length = self.CONFIG['TELEGRAM_CAPTION_LIMIT'] - len(base_message.format(summary=""))
        if available_length < 0:
            available_length = 0

        if len(summary) > available_length:
            truncated_summary = summary[:available_length]

            match = re.search(r'(?s)(.*?[.!?])[^.!?]*$', truncated_summary)
            if match:
                truncated_summary = match.group(1)

            summary = truncated_summary

        message = base_message.format(summary=summary)

        return message, image, link
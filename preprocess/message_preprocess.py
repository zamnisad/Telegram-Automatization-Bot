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
        return re.sub(r"([{}])".format(re.escape(special_chars)), r"\\\1", text)

    async def prepare_post(self):
        template, summary, image, link, ht_idx = self.GenerateBot.get_all()

        summary = str(self.escape_markdown_v2(summary))
        template = str(self.escape_markdown_v2(template))

        hashtags = str(self.escape_markdown_v2(' '.join(self.CONFIG['channels'][self.idx]['hashtags']))).split()

        fixed_top = f"{template}\n\n"
        fixed_tail = f"Подробнее [тут]({link})\n\n\n"
        for i in ht_idx.split():
            fixed_tail += f'{hashtags[i]} '
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
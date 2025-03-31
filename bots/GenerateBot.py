import json
import requests
from bots.RSSBot import RSSBot
from bs4 import BeautifulSoup


class GenerateBot:
    def __init__(self, logger, idx):
        with open('CONFIG.json', 'r', encoding='utf-8') as f:
            self.CONFIG = json.load(f)
        self.logger = logger
        self.idx = idx
        self.RSSBot = RSSBot(f'sent_links_{self.CONFIG["channels"][idx]["url"]}.json', self.logger) # NEED UPDATE

    async def generate_ollama_request(self, prompt):
        try:
            response = requests.post(
                f"{self.CONFIG['model_url']}/api/generate",
                json={
                    "model": self.CONFIG['model'],
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_ctx": 4096
                    }
                }
            )
            if response.status_code == 200:
                result = response.json()
                return result["response"].strip()
            else:
                self.logger.error(f"Ollama error: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Ollama connection error: {str(e)}")
            return None

    async def generate_ollama_summary(self, text):
        text = text[:self.CONFIG["max_text_for_summary"]]
        prompt = self.CONFIG['channels'][self.idx]['rephrase'].replace('\\text', text[:1000])

        return await self.generate_ollama_request(prompt)

    async def choose_ht(self, text):
        prompt = prompt = (
                    "Ты — инструмент для выбора хештегов. Твоя задача строго следующая:\n"
                    "1. Проанализируй предоставленный текст\n"
                    "2. Выбери от 2 до 3 наиболее релевантных хештегов из списка\n"
                    "3. Верни ТОЛЬКО индексы выбранных хештегов через пробел\n\n"
                    "ЖЕСТКИЕ ПРАВИЛА:\n"
                    "- Никаких пояснений, только цифры\n"
                    "- Формат строго: `1 3` или `0 2 4`\n"
                    "- Не добавляй точки, запятые или другие символы\n"
                    "- Если хештеги не подходят, верни два случайных индекса\n\n"
                    f"СПИСОК ХЕШТЕГОВ (индекс: значение):\n"
                    + "\n".join(f"{i}: {ht}" for i, ht in enumerate(self.CONFIG["channels"][self.idx]["hashtags"]))
                    + "\n\n"
                    f"ТЕКСТ ДЛЯ АНАЛИЗА:\n{text[:1000]}\n\n"
                    "ОТВЕТ (только цифры через пробел):"
                )
        return await self.generate_ollama_request(prompt)

    async def generate_ollama_template(self, text):
        prompt = self.CONFIG['channels'][self.idx]['template'].replace('\\len', self.CONFIG['max_summary_length'])
        prompt = prompt.replace('\\text', text[:1000])
        return await self.generate_ollama_request(prompt)

    async def get_all(self):
        entry = self.RSSBot.check_feeds(self.idx)
        clean_text = BeautifulSoup(entry.description, 'html.parser').get_text()
        summary = self.generate_ollama_summary(clean_text)
        template = self.generate_ollama_template(summary)
        ht_idx = self.choose_ht(summary)
        img = self.RSSBot.get_image(entry)

        return template, summary, img, entry.link, ht_idx
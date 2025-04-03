import json
import requests
from bots.RSSBot import RSSBot
from io import BytesIO
from bs4 import BeautifulSoup
from diffusers import DiffusionPipeline
from diffusers import OnnxStableDiffusionPipeline
from transformers import pipeline
import torch
import time


class GenerateBot:
    def __init__(self, logger, idx):
        with open('CONFIG.json', 'r', encoding='utf-8') as f:
            self.CONFIG = json.load(f)
        self.logger = logger
        self.idx = idx
        self.logger.info(f"Инициализирован GenerateBot для канала {self.CONFIG['channels'][idx]['url']}")
        self.RSSBot = RSSBot(f'sent_links_{self.CONFIG["channels"][idx]["url"]}.json', self.logger) # NEED UPDATE
        self.pipe = OnnxStableDiffusionPipeline.from_pretrained(
            self.CONFIG['img_model'],
            torch_dtype=torch.float32,
            provider="CPUExecutionProvider"
        )
        self.short_summary = """
        Тебе необходимо по тексту, который будет передан далее, сгенерировать очень короткое описание, которое будет
        состоять из 3-5 слов, но по которому будет понятен контекст того, о чем текст. 
        Не отправляй ничего, кроме этих слов, без приветствий и всего такого, просто 3-5 слов. 
        Вот сам текст: \\text"""

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
                self.logger.info("Запрос к ollama успешен!")
                return result["response"].strip()
            else:
                self.logger.error(f"Ollama error: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Ollama connection error: {str(e)}")
            return None

    async def generate_ollama_summary(self, text):
        self.logger("Генерация описания...")
        text = text[:self.CONFIG["max_text_for_summary"]]
        prompt = self.CONFIG['channels'][self.idx]['rephrase'].replace('\\text', text[:1000])

        return await self.generate_ollama_request(prompt)

    async def choose_ht(self, text):
        self.logger("")
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
        prompt = self.CONFIG['channels'][self.idx]['template'].replace('\\len', str(self.CONFIG['max_summary_length']))
        prompt = prompt.replace('\\text', text[:1000])
        return await self.generate_ollama_request(prompt)

    async def generate_short_summary(self, text):
        prompt = self.short_summary.replace('\\text', text[:1000])
        return await self.generate_ollama_request(prompt)

    async def generate_image(self, short_summary):
        prompt = f"""
        Telegram post illustration:
        - MAIN: Robot analyzing data on holographic interface
        - STYLE: {self.CONFIG['channels'][self.idx]['style']}
        - DETAILS: {short_summary}
        """

        summarizer = pipeline("summarization", model="Falconsai/text_summarization")
        short_text = summarizer(prompt, max_length=300)[0]['summary_text']

        self.logger.info(f'Creating img for {self.CONFIG["channels"][self.idx]["url"]}')
        image = self.pipe(
            prompt=short_text,
            num_inference_steps=6,
            guidance_scale=1.0,
            width=512,
            height=512
        ).images[0]

        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return img_byte_arr

    async def get_all(self):
        entry = await self.RSSBot.check_feeds(self.idx)
        clean_text = BeautifulSoup(entry.description, 'html.parser').get_text()
        summary = await self.generate_ollama_summary(clean_text)
        template = await self.generate_ollama_template(summary)
        short_sum = await self.generate_short_summary(summary)
        ht_idx = await self.choose_ht(summary)
        img = await self.generate_image(short_sum)

        return template, summary, short_sum, img, entry.link, ht_idx
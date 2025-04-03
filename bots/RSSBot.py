import json
import requests
from bs4 import BeautifulSoup
from io import BytesIO
import feedparser
import asyncio
import socket


socket.setdefaulttimeout(10)

class RSSBot:
    def __init__(self, sent_links, logger):
        self.logger = logger
        with open('CONFIG.json', 'r', encoding='utf-8') as f:
            self.CONFIG = json.load(f)
        self.sent_links = sent_links

    async def get_image(self, entry):
        try:
            soup = BeautifulSoup(entry.description, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and 'src' in img_tag.attrs:
                response = requests.get(img_tag['src'])
                return BytesIO(response.content)
        except Exception as e:
            self.logger.error(f"Image error: {str(e)}")
        return None

    async def check_feeds(self, idx):
        self.logger.info("Начало проверки RSS лент...")
        for url in self.CONFIG['channels'][idx]["rss_urls"]:
            try:
                feed = await asyncio.to_thread(feedparser.parse, url)
                for entry in feed.entries:
                    if entry.link not in self.sent_links:
                        return entry
            except Exception as e:
                self.logger.error(f"Index: {idx}. Ошибка RSS: {str(e)}")
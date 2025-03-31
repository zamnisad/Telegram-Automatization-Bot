import json
import os
import asyncio

"""
Example:
{'token': 'botToken', ДОБАВИТЬ В ENV
'AI link': 'http://localhost:11434',
'channels': [
        {
            'url': '@link',                                     |
            'rss_sources': ['s1', 's2', 's3'],                  |
            'hashtags': ['ht1', 'ht2', 'ht3'],                  |
            'time': ['08:30', '15:10', '19:50', '23:45'],       | user data example (dict)
            'template': 'temp',                                 |
            'rephrase': 'temp',                                 |
            'interval': '1000'                                  |
        },
        ...
    ]
}
"""

# BASE_TEMPLATE ="""Сгенерируй привлекательный шаблон для новостного поста Telegram.
#             Шаблон должен быть не длиннее 5 слов, содержать одно эмодзи вначале и не начинаться с приветствий.
#             Ответ должен состоять только из шаблона. Обязательно на русском языке.
#             Ни в коем случае не используй штуки по типу ... 👉 https://[link] и тд. Вот текст: \n\n\\text"""
# BASE_PHRASE = """Прочти следующий текст и составь краткий, структурированный пересказ. Не нужно составлять оглавление и
#             использовать всякие вещи по типу 'Основные Идеи' 'Суть поста' и тд.
#             Просто перефразируй текст на научно-популярный без лишних вводных фраз. Обязательно на русском языке.
#             Если текст имеет указания на какого то человека, допустим 'меня зовут ...', то учти это в своей формулировке
#             Ответ не должен превышать \\len символов. Вот текст: \n\\text"""
# BASE_INTERVAL = 3600 * 3
# в info.txt: link;rss1,rss2,..,rssN;ht1,ht2,..,htN;time1,time2,..,timeN;template;rephrase;interval;


class SetChannels:
    def __init__(self, filename=None):
        self.filename = filename
        self.BASE_TEMPLATE ="""Сгенерируй привлекательный шаблон для новостного поста Telegram. 
            Шаблон должен быть не длиннее 5 слов, содержать одно эмодзи вначале и не начинаться с приветствий. 
            Ответ должен состоять только из шаблона. Обязательно на русском языке. 
            Ни в коем случае не используй штуки по типу ... 👉 https://[link] и тд. Вот текст: \n\n\\text"""
        self.BASE_PHRASE = """Прочти следующий текст и составь краткий, структурированный пересказ. Не нужно составлять оглавление и
            использовать всякие вещи по типу 'Основные Идеи' 'Суть поста' и тд.
            Просто перефразируй текст на научно-популярный без лишних вводных фраз. Обязательно на русском языке.
            Если текст имеет указания на какого то человека, допустим 'меня зовут ...', то учти это в своей формулировке
            Ответ не должен превышать \\len символов. Вот текст: \n\\text"""
        self.BASE_INTERVAL = 3600 * 3

        self.cfg = []


    async def get_info_from_file(self):
        if not self.filename:
            print("Error: filename=None")
            return
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                info = f.readlines()
            for channel in info:
                tmp_cfg = {}

                all = channel.split(';')

                url = all[0].strip()
                rss = all[1].strip().split(',')
                hashtags = all[2].strip().split(',')
                times = all[3].strip().split(',')
                template = all[4] if all[4] != '-1' else self.BASE_TEMPLATE
                rephrase = all[5] if all[5] != '-1' else self.BASE_PHRASE
                interval = int(all[6].strip()) if all[6] != '-1' else self.BASE_INTERVAL

                tmp_cfg['url'] = url
                tmp_cfg['rss_sources'] = rss
                tmp_cfg['hashtags'] = hashtags
                tmp_cfg['time'] = times
                tmp_cfg['template'] = template
                tmp_cfg['rephrase'] = rephrase
                tmp_cfg['interval'] = interval

                self.cfg.append(tmp_cfg)

    async def get_info_from_cmd(self):
        channels_count = int(input("Введите количество каналов, которое вы хотите добавить: "))
        for i in range(channels_count):
            temp_data = {}
            link = input("Введите ссылку на тгк (пример - @Durov): ")
            rss = input("Через пробел вставьте ссылки на rss источники: ").split()
            hashtags = input("Через пробел введите хэштеги: ").split()
            times = input("Через пробел введите времена постинга (пример - 08:30 9:40): ")
            template = input("Введите запрос для генерации заголовка (введите -1 для "
                             "запроса по умолчанию): ")
            rephrase = input("Введите запрос для генерации краткого описания (введите -1 для "
                             "запроса по умолчанию): ")
            interval = input("Введите интервал для проверки наличия новых постов rss (введите -1 для "
                             "значения по умолчанию): ")
            if template == '-1':
                template = self.BASE_TEMPLATE
            if rephrase == '-1':
                rephrase = self.BASE_PHRASE
            if interval == '-1':
                interval = self.BASE_INTERVAL

            temp_data['url'] = link
            temp_data['rss_sources'] = rss
            temp_data['hashtags'] = hashtags
            temp_data['time'] = times
            temp_data['template'] = template
            temp_data['rephrase'] = rephrase
            temp_data['interval'] = interval

            self.cfg.append(temp_data)

    async def write_to_json(self):
        data = {'token': '8022820972:AAHUIM55DwEEmSTbm_qEiS1qbw77aS1Kzj8',
                'AI link': 'http://localhost:11434',
                'channels': []
                }

        data['channels'].extend(self.cfg)
        with open('CONFIG.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    async def add_to_json(self, data):
        try:
            with open('CONFIG.json', 'r', encoding='utf-8') as f:
                self.cfg = json.load(f)
        except Exception as e:
            print('Error: cannot open json file [read process]: ', e)

        self.cfg['channels'].append(data)
        try:
            with open('CONFIG.json', 'w', encoding='utf-8') as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print('Error: cannot write data to json [write process]: ', e)

if __name__ == '__main__':
    print(asyncio.run(SetChannels().get_info_from_file()))
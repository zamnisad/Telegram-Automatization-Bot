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
            'rss_urls': ['s1', 's2', 's3'],                  |
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

"""
Проанализируй предоставленный текст и создай краткий, но информативный пересказ для Telegram-поста, используя MarkdownV2-разметку. 

Основные требования:
1. Сохрани научно-популярный стиль
2. Выдели ключевые моменты:
   - *Важные идеи* - курсивом
   - **Особо значимые моменты** - жирным
   - `Технические термины` и `код` - обратными кавычками
3. Используй эмодзи для визуального разделения блоков (но не более 3-х на пост)
4. Для цитат используй символ ">"
5. Учитывай контекст (если текст от первого лица - адаптируй)
6. Не нужно писать заголовок, ТОЛЬКО перечисление или заключение
7. Можешь использовать короткие перечисления, как в примере ниже, но не более трех пунктов
8. Длина не должна превышать \\len символов

Твоя задача просто хорошо пересказать то, о чем говорится в сообщении и отправить это без лишних приветствий и так далее,
представь, что ты владелец телеграм канала и твоя задача выложить этот пост

Пример хорошего оформления:
Ученые создали `новую архитектуру GAN`, которая **в 2 раза быстрее** аналогов. 
> "Это изменит подход к генерации изображений"
Суть данного метода заключается в том, что используется смесь старой модели GPT и обучение с учителем.
В статье так же описана реализация того, как **использовать** данную структуру в бизнес задачах!

Основные преимущества:
- Экономия вычислительных ресурсов
- Более стабильное обучение
- Поддержка `Python 3.12+`

Вот текст для анализа:
\\text
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
# в info.txt: link;style;rss1,rss2,..,rssN;ht1,ht2,..,htN;time1,time2,..,timeN;template;rephrase;interval;


class SetChannels:
    def __init__(self, filename=None):
        self.filename = filename
        self.BASE_TEMPLATE = """
Проанализируй предоставленный текст и создай краткий, но информативный пересказ для Telegram-поста, используя MarkdownV2-разметку. 

Основные требования:
1. Сохрани научно-популярный стиль
2. Выдели ключевые моменты:
   - *Важные идеи* - курсивом
   - **Особо значимые моменты** - жирным
   - `Технические термины` и `код` - обратными кавычками
3. Используй эмодзи для визуального разделения блоков (но не более 3-х на пост)
4. Для цитат используй символ ">"
5. Учитывай контекст (если текст от первого лица - адаптируй)
6. Не нужно писать заголовок, ТОЛЬКО перечисление или заключение
7. Можешь использовать короткие перечисления, как в примере ниже, но не более трех пунктов
8. Длина не должна превышать \\len символов

Твоя задача просто хорошо пересказать то, о чем говорится в сообщении и отправить это без лишних приветствий и так далее,
представь, что ты владелец телеграм канала и твоя задача выложить этот пост

Пример хорошего оформления:
Ученые создали `новую архитектуру GAN`, которая **в 2 раза быстрее** аналогов. 
> "Это изменит подход к генерации изображений"
Суть данного метода заключается в том, что используется смесь старой модели GPT и обучение с учителем.
В статье так же описана реализация того, как **использовать** данную структуру в бизнес задачах!

Основные преимущества:
- Экономия вычислительных ресурсов
- Более стабильное обучение
- Поддержка `Python 3.12+`

Вот текст для анализа:
\\text
"""
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
                style = all[1].strip()
                rss = all[2].strip().split(',')
                hashtags = all[3].strip().split(',')
                times = all[4].strip().split(',')
                template = all[5] if all[5] != '-1' else self.BASE_TEMPLATE
                rephrase = all[6] if all[6] != '-1' else self.BASE_PHRASE
                interval = int(all[7].strip()) if all[6] != '-1' else self.BASE_INTERVAL

                tmp_cfg['url'] = url
                tmp_cfg['style'] = style
                tmp_cfg['rss_urls'] = rss
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
            style = input("Введите стиль для изображений к постам на английском языке (пример - Cyberpunk): ")
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
            temp_data['style'] = style
            temp_data['rss_urls'] = rss
            temp_data['hashtags'] = hashtags
            temp_data['time'] = times
            temp_data['template'] = template
            temp_data['rephrase'] = rephrase
            temp_data['interval'] = interval

            self.cfg.append(temp_data)

    @staticmethod
    async def write_to_json(CONFIG):
        with open('CONFIG.json', 'w', encoding='utf-8') as f:
            json.dump(CONFIG, f, ensure_ascii=False, indent=4)

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
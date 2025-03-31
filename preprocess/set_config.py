from preprocess.set_channels import *

CONFIG = {
    "model_url": "http://localhost:11434",
    "telegram_token": "token",
    "model": "llama3",
    "max_summary_length": 500,
    "max_hashtags": 5,
    "max_text_for_summary": 3000,
    "TELEGRAM_CAPTION_LIMIT": 1024
}

async def set_config():
    data = ''
    while True:
        use = input("Введите, какой метод вы хотите использовать:\n1 - запись с файла\n2 - запись с cmd\n\n"
                    "3 - использовать готовый файл\n\nВвод - ")
        if use == '1':
            filename = input('Введите путь до файла с информацией: ')
            sc = SetChannels(filename)
            data = await sc.get_info_from_file()
            break
        elif use == '2':
            sc = SetChannels()
            data = await sc.get_info_from_cmd()
            break
        elif use == '3':
            with open('CONFIG.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            print('Ошибка, введите корректное число!\n\n')
    if use != '3':
        for item in data:
            for k, v in item.items():
                CONFIG[k] = v
        if os.path.exists('CONFIG.json'):
            await sc.add_to_json(data)
        else:
            await sc.write_to_json()


if __name__ == '__main__':
    asyncio.run(set_config())
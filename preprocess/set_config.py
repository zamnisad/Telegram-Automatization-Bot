from preprocess.set_channels import *

CONFIG = {
    "model_url": "http://localhost:11434",
    "telegram_token": "token",
    "model": "llama3",
    "max_summary_length": 500,
    "max_hashtags": 5,
    "max_text_for_summary": 3000,
    "TELEGRAM_CAPTION_LIMIT": 1024,
    "img_model": "CompVis/stable-diffusion-v1-4",
    "channels": []
}
"""img models:
1) SimianLuo/LCM_Dreamshaper_v7 (5 min for all)
2) CompVis/stable-diffusion-v1-4 ()
3) SimianLuo/LCM_Dreamshaper_v7
"""
async def set_config():
    data = []
    while True:
        use = input("Введите, какой метод вы хотите использовать:\n1 - запись с файла\n2 - запись с cmd\n\n"
                    "3 - использовать готовый файл\n\nВвод - ")
        if use == '1':
            filename = input('Введите путь до файла с информацией: ')
            sc = SetChannels(filename)
            await sc.get_info_from_file()
            data = sc.cfg
            break
        elif use == '2':
            sc = SetChannels()
            await sc.get_info_from_cmd()
            data = sc.cfg
            break
        elif use == '3':
            with open('CONFIG.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                sc = SetChannels()
            break
        else:
            print('Ошибка, введите корректное число!\n\n')
    if use != '3':
        flag = str(input('Создать новый CONFIG.json? (Y/N): '))
        for i, item in enumerate(data):
            CONFIG['channels'].append({})
            for k, v in item.items():
                CONFIG['channels'][i][k] = v
        if os.path.exists('CONFIG.json') and flag == 'N':
            await sc.add_to_json(data) # Добавить проверку на то, что текущий канал еще не добавлен
        else:
            await sc.write_to_json(CONFIG)


if __name__ == '__main__':
    asyncio.run(set_config())
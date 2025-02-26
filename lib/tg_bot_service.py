"""
Модуль запуска телеграм-бота
"""
from aiogram import Bot, Dispatcher
import yaml


CONFIG_PATH = "lib/config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
    CONFIG = yaml.load(config_file, Loader=yaml.FullLoader)


def launch_telegram_bot():
    """
    Функция запуска телеграм бота
    """
    bot = Bot(token=CONFIG["TELEGRAM_BOT_TOKEN"])
    dp = Dispatcher()
    dp.run_polling(bot)


if __name__ == '__main__':
    launch_telegram_bot()

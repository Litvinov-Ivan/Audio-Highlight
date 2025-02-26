"""
Модуль со вспомогательными функциями и классами
"""

import copy
import requests
from typing import List
import librosa as lb
import yaml
from numpy import ndarray


CONFIG_PATH = "lib/config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
    CONFIG = yaml.load(config_file, Loader=yaml.FullLoader)


class NotSupportedModelException(Exception):
    """
    Класс исключения, возникающей при попытке загрузки
    неподдерживаемую приложением модель.
    """

    def __init__(
        self,
        model: str,
        msg: str,
    ):
        """
        Конструктор класса NotSupportedModelException.

        :param
        model : str
            Введенная модель
        msg : str
            Сообщение при вызове исключения.
        """
        self.model = model
        self.msg = msg


class FeedbackMessage:
    """
    Класс сообщения формы обратной связи.
    """
    def __init__(
        self,
        name: str,
        message_text: str,
        contact: str,
    ):
        """
        Конструктор класс FeedbackMessage.

        :param
        name : str
            Имя пользователя
        message_text : str
            Сообщение от пользователя
        contact : str
            Контакт пользователя
        """
        self.name = name
        self.message_text = message_text
        self.contact = contact

    def __str__(self):
        line = "-" * 25
        message_string = "Новое сообщение!\n"
        message_string += line
        message_string += f"\nИмя пользователя:\n{self.name}\n"
        message_string += line
        message_string += f"\nКонтакт пользователя:\n{self.contact}\n"
        message_string += line
        message_string += f"\nСообщение:\n{self.message_text}"
        return message_string


async def sort_tracks(
    datas: List[ndarray],
    sample_rates: List[int | float],
) -> List[int]:
    """
    Асинхронная функция сортировки треков по БПМ.

    :param
    data : List[ndarray]
        Список с аудиофайлами.
    sample_rates : List[int | float]
        Список частот дискретизации переданных треков.
    :return:
    indices_new
        Список индексов отсортированных треков.
    """
    datas_local = copy.deepcopy(datas)
    sample_rates_local = copy.deepcopy(sample_rates)

    indices = list(range(len(datas_local)))
    tempos = [
        lb.beat.beat_track(
            y=datas_local[i],
            sr=sample_rates_local[i],
        )[0][0] for i in indices
    ]

    indices_new = []
    # Итеративно ищем самый медленный трек
    # из оставшихся, сохраняем его индекс,
    # а его самого удаляем отовсюду
    while len(indices) > 0:
        cur = tempos.index(min(tempos))
        indices_new.append(indices[cur])
        del indices[cur]
        del tempos[cur]
        del datas_local[cur]
        del sample_rates_local[cur]
    return indices_new


def get_max_area_section(
    graph_list: List[float],
    highlight_duration: int,
) -> int | float:
    """
    Функция для нахождения области графа с максимальной площадью.

    :param
    graph_list : List[float]
        Список с предсказанием модели.
    highlight_duration : int
        Длина искомого хайлайта.
    :return:
    highlight_start : int
        Индекс элемента graph_list, откуда начинается хайлайт.
    """
    highlight_start = 0
    max_area = 0.0
    for i in range(len(graph_list) - highlight_duration):
        cur_area = sum(graph_list[i:i + highlight_duration])
        if cur_area > max_area:
            highlight_start = i
            max_area = cur_area
    return highlight_start


def send_telegram_message(message: FeedbackMessage | str) -> None:
    """
    Функция отправки сообщений с помощью telegram-бота

    :param
    message:FeedbackMessage | str
        Сообщение, которое надо передать в telegram-бот
    """
    url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_BOT_TOKEN']}/sendMessage"
    params = {
        "chat_id": CONFIG["TELEGRAM_CHAT_ID"],
        "text": message
    }
    requests.post(
        url=url, 
        params=params,
    )

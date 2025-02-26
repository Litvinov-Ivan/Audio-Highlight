"""
Модуль выделения хайлайтов из аудиофайлов.
"""

import gc
from math import floor
from typing import List
import librosa as lb
import numpy as np
from lib.model import AudioHighlightsModel
from lib.utils import (
    get_max_area_section,
    NotSupportedModelException,
)


HIGHLIGHT_DURATION_SEC = 30
MAX_TRACK_DURATION_SEC = 200


async def get_highlight(
    track: np.ndarray,
    sample_rate: int | float,
) -> np.ndarray:
    """
    Асинхронная функция выделения хайлайта из переданного аудиофайла.

    :param
    track : numpy.ndarray
        Аудиофайл для выделения хайлайта.
    sample_rate : int | float
        Частота дискретизации переданного трека.
    :return:
    highlight : numpy.ndarray
        Выделенный хайлайт.
    """
    duration = lb.get_duration(
        y=track,
        sr=sample_rate,
    )

    if duration <= HIGHLIGHT_DURATION_SEC:
        return track

    if duration >= MAX_TRACK_DURATION_SEC:
        track = track[: floor(MAX_TRACK_DURATION_SEC * sample_rate)]
        duration = lb.get_duration(
            y=track,
            sr=sample_rate,
        )
    model = AudioHighlightsModel()
    features = await model.extract_features(track)
    prediction = await model.predict(features)

    if model.ONNX_WEIGHTS_PATH.startswith("weights/retrain"):
        highlight_start_sec = get_max_area_section(
            graph_list=prediction,
            highlight_duration=HIGHLIGHT_DURATION_SEC,
        )
    else:
        raise NotSupportedModelException(
            model="Unsupported model",
            msg="Unsupported weights type"
        ) from Exception

    if highlight_start_sec + HIGHLIGHT_DURATION_SEC > duration:
        highlight_start_sec = duration - HIGHLIGHT_DURATION_SEC

    # для исключения переполнения памяти, модель с весами инициируется
    # при каждом выделении хайлайта, а затем удаляется
    # вместе с выделенными фичами после предсказания
    del model
    del features
    gc.collect()

    highlight = track[
        floor(highlight_start_sec * sample_rate): floor(
            (highlight_start_sec + HIGHLIGHT_DURATION_SEC) * sample_rate
        )
    ]
    return highlight


async def get_highlights_list(
    data: List[np.ndarray],
    sample_rates: List[int | float],
) -> List[np.ndarray]:
    """
    Асинхронная функция, принимающая аудиофайлы
    и возвращающая список хайлайтов из них.

    :param
    data : List[np.ndarray]
        Список с аудиофайлами.
    sample_rates : List[int | float]
        Список частот дискретизации переданных треков.
    :return:
    highlights_list : List[numpy.ndarray]
        Список хайлайтов переданных треков.
    """
    highlights_list = []
    for idx, value in enumerate(data):
        highlights_list.append(
            await get_highlight(value, sample_rates[idx])
        )
    return highlights_list

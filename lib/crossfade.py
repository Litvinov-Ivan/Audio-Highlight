"""
Модуль с функциями склеивания треков в плейлист.
"""

from typing import List, Tuple
import librosa as lb
import numpy as np


async def transient_cross(
    data_1: np.ndarray,
    data_2: np.ndarray,
    sample_rate_1: int | float,
    sample_rate_2: int | float,
    cross_len: int | float = 5,
    sigmoid_coef: int | float = 4,
) -> Tuple[np.ndarray, int | float]:
    """
    Асинхронная функция склеивания двух аудиотреков.
    Выбранная транзиента для кроссфейда - сигмоида.

    :param
    data_1 : np.ndarray
        Первый трек.
    data_2 : np.ndarray
        Второй трек.
    sample_rate_1 : int | float
        Частота дискретизации первого трека.
    sample_rate_2 : int | float
        Частота дискретизации первого трека.
    cross_len : int | float = 5
         Длина перекрытия треков при их склейке в секундах.
    sigmoid_coef : int | float = 4
        Крутизна сигмоиды, от величины параметра зависит
        гладкость при переходе от одного трека к другому.
    :return:
    data_merged : numpy.ndarray
        ndarray со склеенными хайлайтами переданных треков.
    sample_rate : int | float
        sample rate конечного аудиофайла.
    """
    # Приводим к одному sample_rate
    sample_rate = min(sample_rate_1, sample_rate_2)
    data_1 = lb.resample(
        y=data_1,
        orig_sr=sample_rate_1,
        target_sr=sample_rate
    )
    data_2 = lb.resample(
        y=data_2,
        orig_sr=sample_rate_2,
        target_sr=sample_rate
    )

    # Выделяем фрагменты, попавшие в переход
    head_1 = data_1[: len(data_1) - cross_len * sample_rate]
    tail_1 = data_1[len(data_1) - cross_len * sample_rate:]
    head_2 = data_2[: cross_len * sample_rate]
    tail_2 = data_2[cross_len * sample_rate:]

    # Плавное уменьшение громкости tail_1
    # и плавное увеличение громкости head_2
    increasing = list(
        map(
            lambda x: 1 / (
                    1 + np.exp(sigmoid_coef - 2 * sigmoid_coef * x)
            ),
            np.linspace(start=0., stop=1., num=len(tail_1))
        )
    )
    decreasing = list(
        map(
            lambda x: 1 - 1 / (
                    1 + np.exp(sigmoid_coef - 2 * sigmoid_coef * x)
            ),
            np.linspace(start=0., stop=1., num=len(head_2))
        )
    )
    head_2 = head_2 * increasing
    tail_1 = tail_1 * decreasing

    return np.concatenate([head_1, head_2 + tail_1, tail_2]), sample_rate


async def crossfade_setlist(
    data: List[np.ndarray],
    sample_rates: List[int | float],
    selected_idxs: List[int],
    cross_len: int | float = 5,
) -> Tuple[np.ndarray, int | float]:
    """
    Асинхронная функция склеивания переданного списка хайлайтов
    в один аудиофайл-плейлист.

    :param
    data : List[np.ndarray]
        Список из переданных хайлайтов.
    sample_rates : List[int | float]
        Список частот дискретизации переданных хайлайтов.
    selected_idxs : List[int]
        Список индексов отсортированных треков.
    cross_len : int | float = 5
        Длина перекрытия треков при склеивании в секундах.
    :return:
    data_merged : np.ndarray
        ndarray со склеенными хайлайтами переданных треков.
    sample_rates_result : int | float
        sample rate конечного аудиофайла с плейлистом.
    """
    if len(data) <= 1:
        return data[0], sample_rates[0]

    data_merged, sample_rates_result = await transient_cross(
        data[selected_idxs[0]],
        data[selected_idxs[1]],
        sample_rates[selected_idxs[0]],
        sample_rates[selected_idxs[1]],
        cross_len,
    )

    for i in selected_idxs[2:]:
        data_merged, sample_rates_result = await transient_cross(
            data_merged,
            data[i],
            sample_rates_result,
            sample_rates[i],
            cross_len,
        )
    return data_merged, sample_rates_result

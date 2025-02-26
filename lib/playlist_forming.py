"""
Модуль с пайплайном формирования плейлиста из хайлайтов загруженнх треков.
"""

from typing import Tuple, List
from numpy import ndarray
from lib.utils import sort_tracks
from lib.highlight import get_highlights_list
from lib.crossfade import crossfade_setlist


async def playlist_pipeline(
    data: List[ndarray],
    sample_rates: List[int | float],
    cross_len: int | float = 5,
) -> Tuple[List[ndarray] | ndarray, int | float]:
    """
    Асинхронная функция по созданию плейлиста из выбранных треков.
    Сначала треки сортируются по БПМ, затем из каждого выделяется хайлайт,
    после чего список хайлайтов склеивается с указанным перекрытием.

    :param
    data : List[ndarray]
        Список с аудиофайлами.
    sample_rates : List[int | float]
        Список частот дискретизации переданных треков.
    cross_len : int | float = 5
        Длина перекрытия треков при их склейке в секундах.
    :return:
    data_merged : numpy.ndarray
        ndarray со склеенными хайлайтами переданных треков.
    sample_rate : int | float
        sample rate конечного аудиофайла с плейлистом.
    """
    selected_idxs = await sort_tracks(
        data,
        sample_rates,
    )
    data = await get_highlights_list(
        data,
        sample_rates,
    )
    data_merged, sample_rate = await crossfade_setlist(
        data,
        sample_rates,
        selected_idxs,
        cross_len,
    )
    return data_merged, sample_rate

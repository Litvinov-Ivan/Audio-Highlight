"""
Основной модуль приложения Audio Highlight.

Запускает веб-сервис на основе Streamlit.
"""

import io
import tempfile
import asyncio
from time import time
from typing import Tuple, List
import librosa as lb
import streamlit as st
import soundfile as sf
import pandas as pd
from aiocache import cached
from numpy import ndarray
from lib.playlist_forming import playlist_pipeline
from lib.highlight import get_highlights_list
from lib.utils import FeedbackMessage, send_telegram_message


@cached()
async def get_playlist(
    files_df: dict
) -> Tuple[List[ndarray] | ndarray, int | float]:
    """
    Кэшируемая асинхронная функция, принимающая словарь с аудиофайлами
    для последующего формирования плейлиста из выделенных хайлайтов.

    :param
    files_df : dict
        Словарь с данными аудиофайлов для обработки. Имеет поля:
            'track_name' - список названий аудиофайлов
            'track_audio' - список аудиофайлов
            'track_sr' - список sample rate аудиофайлов
    :return:
    data_merged : List[ndarray] | ndarray
        ndarray со склеенными хайлайтами переданных треков.
    sample_rate : int | float
        sample rate конечного аудиофайла с плейлистом.
    """
    return await playlist_pipeline(
        data=files_df["track_audio"],
        sample_rates=files_df["track_sr"],
    )


@st.fragment
def download_file(
    audio_tempfile: str,
    filename: str,
):
    """
    Функция для создания кнопки скачивания сгенерированного
    аудиофайла (хайлайта или плейлиста хайлайтов) в веб-сервисе.

    :param
    audio_tempfile : str
        Имя tempfile.
    filename: str
        Имя аудиофайла, переданного сервису для обработки.
    :return: None
    """
    with open(audio_tempfile, "rb") as output_file:
        st.download_button(
            label="Скачать файл",
            data=output_file,
            file_name=f"{filename}_{int(time())}.wav",
            mime="audio/wav",
        )


async def main():
    """
    Основная функция сервиса.

    С помощью streamlit создается веб-сервис,
    принимающий аудиофайлы в формате .mp3 и .wav с возможностью
    выделения хайлайтов и создания плейлиста на их основе.

    :return: None
    """
    def on_submit_click():
        """
        Функция для обновления состояния сессии при нажатии кнопки
        отправки обратной связи.

        :return: None
        """
        if (
                not st.session_state.user_feedback_text or
                not st.session_state.user_name
        ):
            st.session_state["feedback_form_submit_text"] = (
                "Заполните обязательные поля."
            )
        else:
            message = FeedbackMessage(
                name=st.session_state.user_name,
                contact=st.session_state.user_contact,
                message_text=st.session_state.user_feedback_text,
            )
            send_telegram_message(message=message)
            st.session_state["feedback_form_submit_text"] = (
                "Спасибо за Ваш отзыв!"
            )

        st.session_state.user_name = ""
        st.session_state.user_feedback_text = ""
        st.session_state.user_contact = ""

    st.set_page_config(
        page_title="Audio-highlight Demo",
        page_icon=":headphones:",
        layout="wide",
    )
    st.title(":headphones: Audio-highlight Demo")

    # Поле для загрузки треков
    uploaded_files = st.file_uploader(
        "Выберите аудио-файлы для выделения хайлайтов",
        accept_multiple_files=True,
        type=["mp3", "wav"],
    )
    tracks_df = {
        "track_name": [],
        "track_audio": [],
        "track_sr": [],
    }

    for uploaded_file in uploaded_files:
        bytes_data = uploaded_file.read()
        audio, sr = lb.load(path=io.BytesIO(bytes_data))
        tracks_df["track_name"].append(uploaded_file.name)
        tracks_df["track_audio"].append(audio)
        tracks_df["track_sr"].append(sr)

    if len(uploaded_files) > 0:
        tracks_table = st.data_editor(
            pd.DataFrame.from_dict(
                {
                    "track_name": tracks_df["track_name"],
                    "check_box": [True] * len(uploaded_files),
                }
            ),
            column_config={
                "check_box": st.column_config.CheckboxColumn(
                    "Выделить хайлайт?",
                    help="Выделите треки для выделения **хайлайта**",
                    default=False,
                )
            },
        )

        tracks_to_get_highlight = {
            "track_name": [],
            "track_audio": [],
            "track_sr": [],
        }
        for idx, value in enumerate(tracks_table["check_box"]):
            if value:
                for key, value_lst in tracks_df.items():
                    tracks_to_get_highlight[key].append(value_lst[idx])

        # Кнопка для выделения хайлайтов из выбранных треков
        if st.button("Выделить хайлайты из выбранных треков"):
            highlights_lst = await get_highlights_list(
                tracks_to_get_highlight["track_audio"],
                tracks_to_get_highlight["track_sr"],
            )
            for idx, highlight in enumerate(highlights_lst):
                st.write(f"{tracks_to_get_highlight['track_name'][idx]}")
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".wav"
                ) as fp:
                    sf.write(
                        fp.name,
                        highlight,
                        tracks_to_get_highlight["track_sr"][idx],
                    )
                    fp.close()
                    st.audio(
                        highlight,
                        sample_rate=tracks_to_get_highlight["track_sr"][idx],
                    )
                    filename = (
                        f"{tracks_to_get_highlight['track_name'][idx][:-4]}"
                        "_highlight"
                    )
                    download_file(
                        audio_tempfile=fp.name,
                        filename=filename,
                    )

        # Кнопка для формирования из выбранных треков плейлиста
        if st.button("Сформировать плейлист из хайлайтов выбранных треков"):
            playlist, playlist_sr = await get_playlist(
                tracks_to_get_highlight
            )
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav"
            ) as fp:
                sf.write(fp.name, playlist, playlist_sr)
                fp.close()
                st.audio(playlist, sample_rate=playlist_sr)
                download_file(
                    audio_tempfile=fp.name,
                    filename="highlights_playlist"
                )

    with st.expander("Связаться с нами"):
        with st.form("my_form"):
            st.write(
                "**Здесь Вы можете поделиться своими "
                "впечатлениями об Audio-Highlight**"
            )
            st.write("Ваши отзывы помогут сделать сервис еще лучше.")
            name = st.text_input(
                value=None,
                label="name",
                placeholder="Как к Вам можно обращаться? (Обязательное поле)",
                label_visibility="hidden",
                key="user_name",
            )
            feedback_text = st.text_input(
                value=None,
                label="feedback_text",
                placeholder="Ваше сообщение. (Обязательное поле)",
                label_visibility="hidden",
                key="user_feedback_text",
            )
            contact = st.text_input(
                value=None,
                label="contact",
                placeholder="Оставьте контакт, чтобы мы могли Вам ответить.",
                label_visibility="hidden",
                key="user_contact",
            )

            submitted = st.form_submit_button(
                "Отправить",
                on_click=on_submit_click,
            )
            if submitted:
                st.write(st.session_state.feedback_form_submit_text)


if __name__ == "__main__":
    asyncio.run(main())

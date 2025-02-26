"""
Модуль класса, инициализирующего веса обученной нейронной сети,
которая выделяет из аудиотреков хайлайты.
"""

from typing import List
import librosa as lb
import numpy as np
import onnxruntime as rt
from lib.utils import NotSupportedModelException


SR = 22050
N_FFT = 2048
N_HOP = 512
N_MEL = 128

SHAPE = (N_MEL, None, 1)
CHUNK_SIZE = 43
N_CHUNK = 72
N_FRAME = N_CHUNK * CHUNK_SIZE
FRAME_PER_SEC = SR / N_HOP
SEC_PER_CHUNK = round(CHUNK_SIZE / FRAME_PER_SEC)


class AudioHighlightsModel:
    """
    Класс модели Audio Highlight, инициализирущий веса нейронной сети,
    выделяющий необходимые признаки из аудиофайлов и осуществляющий
    предсказание хайлайта трека.

    :param
    model_type : str = "onnx"
        Тип модели. По умолчанию приложение поддерживает инициализацию
        и инференс только .onnx моделей.
        Инференс происходит на CPU.
    """

    ONNX_WEIGHTS_PATH = "weights/weights.onnx"

    def __init__(
        self,
        model_type: str = "onnx",
    ):
        """
        Конструктор класса AudioHighlightsModel
        :param
        model_type : str = "onnx"
            Тип модели. По умолчанию приложение поддерживает инициализацию
            и инференс только .onnx моделей.
        """
        self.model_type = model_type
        try:
            self.model = rt.InferenceSession(self.ONNX_WEIGHTS_PATH)
            self.input_name = self.model.get_inputs()[0].name
        except Exception as e:
            raise NotSupportedModelException(
                model=self.model_type,
                msg=str(e)
            ) from e

    @staticmethod
    async def extract_features(
        file: np.ndarray,
    ) -> np.ndarray:
        """
        Статическая асинхронная функция выделения признаков из аудиофайла.

        :param
        file : numpy.ndarray
            Аудиофайл.
        :return:
        feature_crop : numpy.ndarray
            Выделенные из аудиофайла признаки.
        """
        data = lb.feature.melspectrogram(
            y=file,
            sr=SR,
            n_fft=N_FFT,
            hop_length=N_HOP,
            power=1,
            n_mels=N_MEL,
            fmin=20,
            fmax=5000,
        )
        data = np.reshape(data, (data.shape[0], data.shape[1], 1))
        feature_length = len(data[1])
        remain = feature_length % 9
        remain_np = np.zeros([128, 9 - remain, 1])
        feature_crop = np.concatenate((data, remain_np), axis=1)
        feature_crop = np.expand_dims(feature_crop, axis=0)
        return feature_crop

    async def predict(
        self,
        track_features: np.ndarray,
    ) -> List[float]:
        """
        Асинхронная функция предсказания хайлайта
        на основе переданных признаков.

        :param
        track_features : numpy.ndarray
            Выделенные из аудиофайла признаки.
        :return:
        prediction: List[float]
            Предсказание нейросети хайлайта.
        """
        try:
            return self.model.run(
                None, {self.input_name: track_features.astype(np.float32)}
            )[0][0].tolist()
        except Exception as e:
            raise NotSupportedModelException(
                model=self.model_type,
                msg="Not supported model type"
            ) from e

    async def extract_predict(
        self,
        file: np.ndarray,
    ) -> List[float]:
        """
        Асинхронная функция выделения и предсказания
        хайлайта сразу из аудиофайла.

        :param
        file : numpy.ndarray
            Аудиофайл.
        :return:
        prediction: List[float] | None
            Предсказание нейросети хайлайта.
        """
        features = await self.extract_features(file)
        return await self.predict(features)

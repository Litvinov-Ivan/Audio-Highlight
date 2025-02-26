"""
Модуль с Watchdog-ботом, следящим за статусом докер-контейнеров сервиса.
"""
import os
import logging
import docker
import asyncio
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from utils import send_telegram_message


# Инициализация клиента Docker
client = docker.from_env()
DOCKER_CONTAINER_NAMES = {
    "app": None,
    "nginx-entrypoint": None,
}


class DockerContainerHandler(FileSystemEventHandler):
    """
    Класс обработчика событий смены статусов контейнеров
    """
    def on_modified(self, event):
        """
        Метод обработки событий в случае изменения статусов контейнеров
        """
        for key, value in DOCKER_CONTAINER_NAMES.items():
            msg = f"Checking container {key} on modified."
            try:
                container = client.containers.get(key)
            except Exception as e:
                msg += (
                    f"\nThere is no running containers with name {key}!\n"
                    f"Something happened, check server!"
                )
                logging.exception(msg)
                logging.exception(e)
                send_telegram_message(msg)
            else:
                if value != container.status:
                    msg += (
                        f"\nContainer name: {container.name}\n"
                        f"Container status: {container.status}"
                    )
                    logging.exception(msg)
                    send_telegram_message(msg)
                    DOCKER_CONTAINER_NAMES[key] = container.status


async def watchdog_bot():
    """
    Функция запуска Watchdog-бота
    """
    # Настройка логгирования
    logging.basicConfig(level=logging.INFO)

    for key, value in DOCKER_CONTAINER_NAMES.items():
        container = client.containers.get(key)
        DOCKER_CONTAINER_NAMES[key] = container.status
        send_telegram_message(
            f"Polling containers check.\n"
            f"Container name: {key}\n"
            f"Container status: {container.status}"
        )

    observer = PollingObserver()

    # Создание экземпляра обработчика событий и наблюдателя
    event_handler = DockerContainerHandler()
    observer.schedule(
        event_handler,
        path=os.path.dirname("/var/run/docker.sock"),
        recursive=False
    )
    observer.start()

    try:
        # Запуск цикла наблюдения
        while True:
            pass
    except KeyboardInterrupt:
        # Остановка всех наблюдателей
        event_handler.stop()
    event_handler.join()


if __name__ == "__main__":
    asyncio.run(watchdog_bot())

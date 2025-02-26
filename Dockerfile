FROM python:3.10.2

# Перенос содержимого проекта в директорию образа
COPY . /app
WORKDIR /app

# Установка зависимостей
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Исполняемая при поднятии контейнера команда
CMD ["python", "-m", "streamlit", "run", "app.py"]
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

# Получаем API ключи из переменных окружения
currentsapi_key = os.getenv("CURRENTS_API_KEY")  # Устанавливаем ключ Currents API из переменной окружения

# Проверяем, что API ключ задан, иначе выбрасываем ошибку
if not currentsapi_key:
    raise ValueError("Переменная окружения CURRENTS_API_KEY должна быть установлена")

class Topic(BaseModel):
    topic: str  # Модель данных для получения темы в запросе

# Функция для получения последних новостей на заданную тему
def get_recent_news(topic: str):
    url = "https://api.currentsapi.services/v1/latest-news"  # URL API для получения новостей
    params = {
        "language": "en",  # Задаем язык новостей
        "keywords": topic,  # Ключевые слова для поиска новостей
        "apiKey": currentsapi_key  # Передаем API ключ
    }
    response = requests.get(url, params=params)  # Выполняем GET-запрос к API
    if response.status_code != 200:
        # Если статус код не 200, выбрасываем исключение с подробностями ошибки
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {response.text}")
    
    # Извлекаем новости из ответа, если они есть
    news_data = response.json().get("news", [])
    if not news_data:
        return "Свежих новостей не найдено."  # Сообщение, если новости отсутствуют
    
    # Возвращаем заголовки первых 5 новостей, разделенных переносами строк
    return "\n".join([article["title"] for article in news_data[:5]])

# Функция для генерации контента на основе темы и новостей
def generate_content(topic: str):
    recent_news = get_recent_news(topic)  # Получаем последние новости по теме
    return {
            "topic": topic,
            "recent_news": recent_news
            }

@app.post("/generate-post")
async def generate_post_api(topic: Topic):
    # Обрабатываем запрос на генерацию поста
    return generate_content(topic.topic)

@app.get("/")
async def root():
    # Корневой эндпоинт для проверки работоспособности сервиса
    return {"message": "Service is running"}

@app.get("/heartbeat")
async def heartbeat_api():
    # Эндпоинт проверки состояния сервиса
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    # Запуск приложения с указанием порта
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)

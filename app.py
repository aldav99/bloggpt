import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests
from typing import Dict, Any

app = FastAPI()

# Получаем API ключи из переменных окружения
openai.api_key = os.getenv("OPENAI_API_KEY")
currentsapi_key = os.getenv("CURRENTS_API_KEY")

if not openai.api_key or not currentsapi_key:
    raise ValueError("Переменные окружения OPENAI_API_KEY и CURRENTS_API_KEY должны быть установлены")

class Topic(BaseModel):
    topic: str

def get_recent_news(topic: str) -> str:
    url = "https://api.currentsapi.services/v1/latest-news"
    params = {
        "language": "en",
        "keywords": topic,
        "apiKey": currentsapi_key
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {response.text}")
    
    news_data = response.json().get("news", [])
    if not news_data:
        return "Свежих новостей не найдено."
    
    return "\n".join([article["title"] for article in news_data[:5]])

def generate_image(prompt: str) -> str:
    """Генерирует изображение через DALL-E и возвращает URL"""
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=f"Иллюстрация для статьи в Telegram на тему: {prompt}. "
                   "Изображение должно быть ярким, привлекательным и соответствовать теме. "
                   "Стиль: цифровое искусство, подходящее для новостного канала.",
            n=1,
            size="1024x1024",
            quality="standard"
        )
        return response.data[0].url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации изображения: {str(e)}")

def generate_content(topic: str) -> Dict[str, Any]:
    recent_news = get_recent_news(topic)
    
    try:
        # Генерация заголовка
        title = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "user", 
                "content": f"Придумайте заголовок для статьи на тему '{topic}' с учётом новостей:\n{recent_news}"
            }],
            max_tokens=20,
            temperature=0.5
        ).choices[0].message.content.strip()

        # Генерация мета-описания
        meta_description = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "user", 
                "content": f"Напишите мета-описание для статьи с заголовком: '{title}'"
            }],
            max_tokens=30,
            temperature=0.5
        ).choices[0].message.content.strip()

        # Генерация контента статьи
        post_content = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "user", 
                "content": f"""Напишите статью на тему '{topic}', используя новости:\n{recent_news}.
                Требования:
                1. Информативная структура
                2. 1500-3000 символов
                3. Подзаголовки
                4. Анализ трендов
                5. Вступление, основная часть, заключение
                6. Примеры из новостей"""
            }],
            max_tokens=1500,
            temperature=0.5
        ).choices[0].message.content.strip()

        # Генерация изображения
        image_prompt = f"{title}. {meta_description}"
        image_url = generate_image(image_prompt)

        return {
            "title": title,
            "meta_description": meta_description,
            "post_content": post_content,
            "image_url": image_url,
            "image_prompt": image_prompt  # Для отладки и логирования
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента: {str(e)}")

@app.post("/generate-post")
async def generate_post_api(topic: Topic):
    return generate_content(topic.topic)

@app.get("/")
async def root():
    return {"message": "Service is running"}

@app.get("/heartbeat")
async def heartbeat_api():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)

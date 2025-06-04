from fastapi import FastAPI, Request, HTTPException
import httpx  # HTTP клиент для отправки запросов в n8n
import os

app = FastAPI()

# URL вашего n8n вебхука (лучше взять из переменных окружения)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "YOUR_N8N_WEBHOOK_TEST_URL_HERE") # Замените на ваш реальный n8n Test URL

@app.get("/")
async def read_root():
    return {"Hello": "World"} # Это, вероятно, уже есть в вашем шаблоне

# Новый эндпоинт для приема данных от MTS Exolve
@app.post("/exolve-incoming-call/") # Можете назвать эндпоинт как угодно
async def handle_exolve_call(request: Request):
    call_data = {}
    try:
        # Попытка получить JSON данные из запроса от Exolve
        call_data = await request.json()
    except Exception as e:
        # Если не JSON, можно попробовать получить form data или просто логировать
        print(f"Could not parse JSON from Exolve: {e}")
        # Можно передать пустой объект или какую-то базовую информацию
        # call_data = {"error": "No JSON payload from Exolve", "raw_body": await request.body()}


    print(f"Received call data: {call_data}") # Логируем полученные данные

    # Отправляем данные в n8n
    if not N8N_WEBHOOK_URL or "YOUR_N8N_WEBHOOK_TEST_URL_HERE" in N8N_WEBHOOK_URL : # Проверка, что URL установлен
         print("N8N_WEBHOOK_URL не установлен или используется плейсхолдер. Проверьте переменную окружения.")
         # Можно вернуть ошибку или обработать по-другому
         raise HTTPException(status_code=500, detail="N8N webhook URL not configured on server side")


    async with httpx.AsyncClient() as client:
        try:
            response_to_n8n = await client.post(N8N_WEBHOOK_URL, json={
                "source": "railway_fastapi_app",
                "event_type": "incoming_call_exolve",
                "exolve_data": call_data # Передаем данные от Exolve в n8n
            })
            response_to_n8n.raise_for_status() # Проверит на HTTP ошибки (4xx, 5xx)
            print(f"Successfully forwarded data to n8n, status: {response_to_n8n.status_code}")
        except httpx.HTTPStatusError as exc:
            print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
            # Можно добавить дополнительную обработку ошибок здесь
            raise HTTPException(status_code=502, detail="Failed to forward request to n8n")
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")
            raise HTTPException(status_code=502, detail="An error occurred while connecting to n8n")

    # Что вернуть MTS Exolve? Это зависит от того, что ожидает Exolve.
    # Пока просто вернем подтверждение.
    return {"status": "received", "message": "Call data forwarded to n8n"}

# Убедитесь, что у вас установлен httpx:
# pip install httpx
# и добавьте его в ваш файл requirements.txt

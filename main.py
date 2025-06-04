# main.py (Фрагменты для интеграции)

# 1. Убедитесь, что эти импорты присутствуют в начале вашего main.py
import os
import httpx  # Для отправки HTTP-запросов
import asyncio # Может понадобиться для фоновых задач (опционально)
from fastapi import FastAPI, Request, HTTPException, Response # Response может понадобиться для ответа телефонии

# ---------------------------------------------------------------------------
# 2. Загрузка URL для n8n из переменных окружения
#    (У вас это уже есть, просто убедитесь, что актуально)
# ---------------------------------------------------------------------------
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')


# ---------------------------------------------------------------------------
# 3. Вспомогательная функция для отправки данных в n8n
#    (Разместите эту функцию где-нибудь в вашем main.py, например, после импортов
#     или перед определением ваших эндпоинтов FastAPI)
# ---------------------------------------------------------------------------
async def forward_to_n8n(event_name: str, payload: dict):
    """
    Асинхронно отправляет данные на вебхук n8n.

    Args:
        event_name (str): Название события для n8n (например, "incoming_call_received").
        payload (dict): Данные, которые нужно отправить в n8n.

    Returns:
        bool: True, если отправка была успешной (HTTP 2xx), иначе False.
    """
    if not N8N_WEBHOOK_URL:
        print("N8N_WEBHOOK_URL не настроен в переменных окружения. Пропуск отправки в n8n.")
        return False

    # Конфигурация таймаута (например, 10 секунд общий, 5 на соединение)
    timeout_config = httpx.Timeout(10.0, connect=5.0)
    
    # Данные, которые будут отправлены в n8n
    data_to_send = {
        "source": "fastapi_voice_agent_app", # Можете изменить этот идентификатор
        "event_type": event_name,
        "data": payload
    }

    print(f"Попытка отправки данных в n8n для события '{event_name}'. URL: {N8N_WEBHOOK_URL}")
    # print(f"Отправляемые данные в n8n: {data_to_send}") # Раскомментируйте для детального логирования данных

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=data_to_send,
                timeout=timeout_config
            )
            response.raise_for_status()  # Вызовет исключение для HTTP-ошибок 4xx/5xx
            print(f"Данные успешно отправлены в n8n для события '{event_name}', статус: {response.status_code}")
            return True
        except httpx.HTTPStatusError as exc:
            # Ошибка от сервера n8n (например, 400, 401, 404, 500 от n8n)
            print(f"Ошибка HTTP при отправке в n8n для '{event_name}': Статус {exc.response.status_code} от {exc.request.url!r}. Ответ: {exc.response.text[:500]}")
        except httpx.RequestError as exc:
            # Ошибка соединения (DNS, таймаут соединения, соединение отклонено и т.д.)
            print(f"Ошибка соединения при отправке в n8n для '{event_name}': {exc!r} при запросе к {exc.request.url!r}.")
        except Exception as e:
            # Другие неожиданные ошибки
            print(f"Неожиданная ошибка при отправке в n8n для '{event_name}': {e!r}")
    return False

# ---------------------------------------------------------------------------
# 4. Ваш существующий экземпляр FastAPI
#    (У вас это `app = FastAPI()`)
# ---------------------------------------------------------------------------
# app = FastAPI() # У вас это уже есть

# ---------------------------------------------------------------------------
# 5. Модификация вашего эндпоинта для входящих звонков
#    Найдите ваш эндпоинт, который обрабатывает входящие вызовы от MTS Exolve.
#    Судя по скриншотам, у вас есть `@app.post("/incoming_call")`.
#    Вам нужно будет добавить вызов `forward_to_n8n` внутри него.
# ---------------------------------------------------------------------------

# Пример того, как мог бы выглядеть ваш модифицированный эндпоинт:
# ЗАМЕНИТЕ ЭТОТ ПРИМЕР НА ВАШ РЕАЛЬНЫЙ ЭНДПОИНТ С ИНТЕГРАЦИЕЙ

# @app.post("/incoming_call") # Или как называется ваш эндпоинт от Exolve
# async def handle_incoming_exolve_call(request: Request):
#     # --- Начало вашей существующей логики обработки входящего звонка ---
#     print("Получен входящий вызов на /incoming_call...")
#     call_event_data = {} # Сюда соберите данные, которые хотите отправить в n8n
#     raw_body_for_n8n = {} # Данные для отправки в n8n

#     try:
#         # Попытка получить данные из запроса (адаптируйте под формат от MTS Exolve)
#         # Exolve может отправлять данные как JSON, form-data или в другом формате.
#         # Это нужно проверить в документации Exolve или тестовым путем.
#         content_type = request.headers.get("content-type", "").lower()

#         if "application/json" in content_type:
#             call_event_data = await request.json()
#             raw_body_for_n8n = call_event_data # Отправляем все тело JSON
#             print(f"Данные входящего звонка (JSON): {call_event_data}")
#         elif "application/x-www-form-urlencoded" in content_type:
#             form_data = await request.form()
#             call_event_data = dict(form_data)
#             raw_body_for_n8n = call_event_data # Отправляем все данные формы
#             print(f"Данные входящего звонка (Form Data): {call_event_data}")
#         else:
#             # Если формат неизвестен, можно попробовать прочитать тело как байты
#             # и передать его или его часть.
#             body_bytes = await request.body()
#             # raw_body_for_n8n = {"raw_body": body_bytes.decode('utf-8', errors='ignore')} # Пример
#             print(f"Входящий звонок с Content-Type: {content_type}. Тело (первые 200 байт): {body_bytes[:200]}")
#             # Решите, что отправлять в n8n в этом случае.
#             # Для примера, можно отправить информацию о неизвестном формате
#             raw_body_for_n8n = {"error": "Unknown content type", "content_type_received": content_type}


#         # ... (здесь ваша основная логика обработки звонка: Ultravox, Pinecone, и т.д.) ...
#         # ... (формирование ответа для MTS Exolve) ...

#     except Exception as e:
#         print(f"Ошибка при обработке входящего звонка: {e}")
#         # Важно вернуть корректный ответ для MTS Exolve даже в случае ошибки
#         # return Response(content="Произошла ошибка", status_code=500, media_type="text/plain") # Пример
#         raise HTTPException(status_code=500, detail=f"Ошибка обработки вызова: {str(e)}")

#     # --- Конец вашей основной логики обработки ---


#     # --- Отправка данных в n8n ---
#     # Отправляем собранные данные (raw_body_for_n8n) в n8n.
#     # Это можно сделать асинхронно, чтобы не задерживать ответ для MTS Exolve,
#     # если результат отправки в n8n не влияет на ответ телефонии.
#     if raw_body_for_n8n: # Убедимся, что есть что отправлять
#         # Если не нужно ждать результата отправки в n8n для ответа Exolve:
#         # asyncio.create_task(forward_to_n8n(event_name="mts_exolve_incoming_call", payload=raw_body_for_n8n))
#         # Если нужно дождаться (например, для логирования или если есть зависимость):
#         n8n_forward_success = await forward_to_n8n(event_name="mts_exolve_incoming_call", payload=raw_body_for_n8n)
#         if n8n_forward_success:
#             print("Данные о входящем звонке Exolve успешно переданы в n8n.")
#         else:
#             print("Не удалось передать данные о входящем звонке Exolve в n8n.")
#     else:
#         print("Нет данных для отправки в n8n по входящему звонку Exolve.")
#     # --- Конец отправки данных в n8n ---


#     # --- Формирование и возврат ответа для MTS Exolve ---
#     # ВАЖНО: Этот ответ должен быть в том формате, который ожидает MTS Exolve.
#     # Это может быть JSON, XML (как TwiML для Twilio) или что-то еще.
#     # Проверьте документацию MTS Exolve.
#     # Пример ответа JSON:
#     print("Отправка ответа для MTS Exolve...")
#     return {"status": "success", "message": "Call received and processing initiated"}
#     # Пример ответа XML (если Exolve ожидает что-то вроде TwiML):
#     # exolve_response_xml = "<Response><Say>Спасибо за ваш звонок.</Say></Response>"
#     # return Response(content=exolve_response_xml, media_type="application/xml")


# ---------------------------------------------------------------------------
# 6. Убедитесь, что в вашем `requirements.txt` есть строка:
#    httpx
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 7. Убедитесь, что переменная окружения N8N_WEBHOOK_URL установлена
#    в настройках вашего сервиса на Railway с корректным URL вашего n8n вебхука.
# ---------------------------------------------------------------------------

# ... (остальной ваш код main.py, включая запуск uvicorn, если он там)
# if __name__ == "__main__":
#     import uvicorn
#     # PORT у вас загружается из os.environ, это хорошо
#     uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

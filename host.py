import asyncio
import websockets
import json
import pyautogui


async def send_click():
    # Получаем разрешение экрана хоста
    screen_width, screen_height = pyautogui.size()

    # Получаем текущие координаты мыши
    x, y = pyautogui.position()

    # Конвертируем в проценты
    percent_x = (x / screen_width) * 100
    percent_y = (y / screen_height) * 100

    # Отправляем проценты на сервер
    async with websockets.connect("ws://localhost:8765") as ws:
        await ws.send(json.dumps({
            "type": "click",
            "percent_x": percent_x,
            "percent_y": percent_y
        }))


asyncio.run(send_click())
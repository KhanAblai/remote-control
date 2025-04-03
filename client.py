import asyncio
import websockets
import json
import time
import pyautogui
import ntplib
from datetime import datetime
from client_core import ClientCore

# NTP-синхронизация
ntp_offset = 0.0


def sync_ntp():
    global ntp_offset
    try:
        client = ntplib.NTPClient()
        response = client.request('pool.ntp.org')
        ntp_offset = response.tx_time - time.time()
        print(f"Время синхронизировано. Смещение: {ntp_offset:.3f} сек")
    except:
        print("Ошибка синхронизации с NTP!")
        ntp_offset = 0.0


def get_ntp_time():
    return time.time() + ntp_offset


sync_ntp()  # Синхронизация при старте


async def main():
    core = ClientCore()
    async with websockets.connect("ws://localhost:8765") as websocket:
        client_id = await core.connect("ws://localhost:8765")
        print(f"Ваш ID: {client_id}")

        # Обработчик ввода команд
        async def input_handler():
            while True:
                try:
                    cmd = await asyncio.get_event_loop().run_in_executor(None, input, "> ")

                    if cmd == "showclients":
                        await websocket.send(json.dumps({"type": "showclients"}))

                    elif "click" in cmd:
                        parts = cmd.replace("after", "").split()
                        targets = parts[0]
                        x, y, *delay = parts[2], parts[3], (int(parts[5]) if "after" in cmd else 0)

                        target_time = get_ntp_time() + (delay[0] if delay else 0)

                        await websocket.send(json.dumps({
                            "type": "command",
                            "targets": targets.split(",") if "," in targets else "all",
                            "command": {
                                "type": "click",
                                "x": int(x),
                                "y": int(y),
                                "percent_x": (int(x) / pyautogui.size().width) * 100,
                                "percent_y": (int(y) / pyautogui.size().height) * 100,
                                "time": target_time
                            }
                        }))

                except Exception as e:
                    print(f"Ошибка ввода: {e}. Формат: 'all:click X Y after D'")

        # Обработчик сообщений
        async def message_handler():
            async for message in websocket:
                data = json.loads(message)

                if data["type"] == "client_list":
                    print("\nАктивные клиенты:")
                    for cid in data["clients"]:
                        print(f" - {cid}")

                elif data["type"] == "click":
                    screen_w, screen_h = pyautogui.size()
                    x = (data["percent_x"] / 100) * screen_w
                    y = (data["percent_y"] / 100) * screen_h

                    delay = max(0, data["time"] - get_ntp_time())
                    if delay > 0:
                        await asyncio.sleep(delay)

                    pyautogui.click(x, y)
                    print(f"Клик в ({int(x)}, {int(y)}) {'с задержкой ' + str(delay) if delay else ''}")

        await asyncio.gather(input_handler(), message_handler())


if __name__ == "__main__":
    asyncio.run(main())

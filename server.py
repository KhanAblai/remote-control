import asyncio
import websockets
import json
import time
from uuid import uuid4

clients = {}


async def handle_connection(websocket, path):  # Оба параметра обязательны!
    client_id = str(uuid4())
    clients[client_id] = {"ws": websocket, "ping": 0}
    print(f"[+] Клиент {client_id} подключился")

    try:
        await websocket.send(json.dumps({
            "type": "client_id",
            "id": client_id
        }))

        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "ping":
                clients[client_id]["ping"] = (time.time() - data["client_time"]) * 1000
                await websocket.send(json.dumps({
                    "type": "pong",
                    "clients": {k: v["ping"] for k, v in clients.items()}
                }))

            elif data["type"] == "command":
                targets = data["targets"]
                command = data["command"]
                current_time = time.time()

                for target_id in (clients.keys() if targets == "all" else targets):
                    if target_id in clients:
                        client = clients[target_id]
                        send_time = command["time"] - (client["ping"] / 1000)
                        delay = max(0, send_time - current_time)
                        await asyncio.sleep(delay)
                        await client["ws"].send(json.dumps(command))

            elif data["type"] == "showclients":
                await websocket.send(json.dumps({
                    "type": "client_list",
                    "clients": list(clients.keys())
                }))

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if client_id in clients:
            del clients[client_id]
            print(f"[-] Клиент {client_id} отключился")


async def main():
    async with websockets.serve(
            handle_connection,
            "0.0.0.0",
            8765
    ):
        print("Сервер запущен на ws://0.0.0.0:8765")
        await asyncio.Future()


asyncio.run(main())
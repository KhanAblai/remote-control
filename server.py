import asyncio
import websockets
import json
import time
import logging
from uuid import uuid4

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
    ]
)
logger = logging.getLogger(__name__)

clients = {}


async def handle_connection(websocket, path):
    client_id = str(uuid4())
    clients[client_id] = {"ws": websocket, "ping": 0}
    logger.info(f"Client connected: {client_id}")

    try:
        # Отправляем ID клиенту
        await websocket.send(json.dumps({
            "type": "client_id",
            "id": client_id
        }))

        # Основной цикл обработки сообщений
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.debug(f"Received message: {data}")

                # Обработка разных типов сообщений
                if data["type"] == "ping":
                    await handle_ping(client_id, data)
                elif data["type"] == "command":
                    await handle_command(data)
                elif data["type"] == "showclients":
                    await handle_show_clients(websocket)
                else:
                    logger.warning(f"Unknown message type: {data['type']}")

            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)

    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Connection error: {str(e)}", exc_info=True)
    finally:
        if client_id in clients:
            del clients[client_id]
            logger.info(f"Client removed: {client_id}")


async def handle_ping(client_id, data):
    """Обработка ping-сообщений"""
    clients[client_id]["ping"] = (time.time() - data["client_time"]) * 1000
    await clients[client_id]["ws"].send(json.dumps({
        "type": "pong",
        "clients": {k: v["ping"] for k, v in clients.items()}
    }))


async def handle_command(data):
    """Обработка команд"""
    command = data["command"]
    current_time = time.time()

    targets = data["targets"]
    if targets == "all":
        targets = list(clients.keys())

    for target_id in targets:
        if target_id in clients:
            try:
                client = clients[target_id]
                send_time = command["time"] - (client["ping"] / 1000)
                delay = max(0, send_time - current_time)

                logger.debug(f"Scheduling command for {target_id} with delay {delay:.2f}s")
                await asyncio.sleep(delay)

                await client["ws"].send(json.dumps(command))
                logger.debug(f"Command sent to {target_id}")

            except Exception as e:
                logger.error(f"Error sending command to {target_id}: {str(e)}")


async def handle_show_clients(websocket):
    """Отправка списка клиентов"""
    await websocket.send(json.dumps({
        "type": "client_list",
        "clients": list(clients.keys())
    }))


async def main():
    try:
        async with websockets.serve(
                handle_connection,
                "0.0.0.0",
                8765,
                ping_interval=None,
                logger=logger
        ):
            logger.info("Server started on ws://0.0.0.0:8765")
            await asyncio.Future()

    except Exception as e:
        logger.critical(f"Server failed to start: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
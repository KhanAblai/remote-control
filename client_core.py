import asyncio
import websockets
import json
import time
import pyautogui
import ntplib

class ClientCore:
    def __init__(self):
        self.ntp_offset = 0.0
        self.websocket = None
        self.client_id = None
        self.sync_ntp()

    def sync_ntp(self):
        try:
            client = ntplib.NTPClient()
            response = client.request('pool.ntp.org')
            self.ntp_offset = response.tx_time - time.time()
        except:
            self.ntp_offset = 0.0

    def get_ntp_time(self):
        return time.time() + self.ntp_offset

    async def connect(self, uri):
        self.websocket = await websockets.connect(uri)
        message = await self.websocket.recv()
        data = json.loads(message)
        if data["type"] == "client_id":
            self.client_id = data["id"]
        return self.client_id

    async def send_command(self, targets, x, y, delay):
        target_time = self.get_ntp_time() + delay
        await self.websocket.send(json.dumps({
            "type": "command",
            "targets": targets,
            "command": {
                "type": "click",
                "x": x,
                "y": y,
                "percent_x": (x / pyautogui.size().width) * 100,
                "percent_y": (y / pyautogui.size().height) * 100,
                "time": target_time
            }
        }))
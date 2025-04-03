import websockets
import json
import time
import platform
import tkinter as tk
from tkinter import ttk, messagebox
from client_core import ClientCore
import asyncio
import pyperclip
from threading import Thread

if platform.system() == "Windows":
    from ctypes import windll

    windll.shcore.SetProcessDpiAwareness(1)


class ClickControlApp(tk.Tk):
    def create_main_menu(self):
        self.clear_window()
        ttk.Button(
            self,
            text="Подключиться к серверу",
            command=lambda: self.run_async(self.connect_to_server())
        ).pack(pady=20)

        # Новая кнопка скачивания
        ttk.Button(
            self,
            text="Скачать клиент",
            command=self.download_client
        ).pack(pady=10)

    def show_os_selection(self):
        """Окно выбора операционной системы"""
        os_window = tk.Toplevel(self)
        os_window.title("Выбор ОС")

        ttk.Label(os_window, text="Выберите вашу операционную систему:").pack(pady=10)

        # Кнопки для Windows и Linux
        ttk.Button(
            os_window,
            text="Windows",
            command=lambda: self.download_client("windows")
        ).pack(pady=5)

        ttk.Button(
            os_window,
            text="Linux",
            command=lambda: self.download_client("linux")
        ).pack(pady=5)

    def download_client(self, os_type):
        """Открытие ссылки для скачивания"""
        import webbrowser
        base_url = "http://64.227.113.220:8080/download"

        if os_type == "windows":
            webbrowser.open(f"{base_url}/windows")
        elif os_type == "linux":
            webbrowser.open(f"{base_url}/linux")
        else:
            messagebox.showerror("Ошибка", "Неизвестный тип ОС")
    def __init__(self):
        super().__init__()
        self.core = ClientCore()
        self.title("Remote Click Controller")
        self.geometry("500x400")

        # Инициализация асинхронного цикла
        self.loop = asyncio.new_event_loop()
        self.websocket = None
        self.client_id = None
        self.clients_data = {}

        # Инициализация интерфейса
        self._create_widgets()
        self._start_async_loop()

        # Обработчик закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _create_widgets(self):
        """Создание начального интерфейса"""
        self.create_main_menu()

    def _start_async_loop(self):
        """Запуск асинхронного цикла в отдельном потоке"""
        self.thread = Thread(target=self.run_async_loop, daemon=True)
        self.thread.start()

    def run_async_loop(self):
        """Запуск асинхронного цикла"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def on_close(self):
        """Обработчик закрытия приложения"""
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.destroy()

    def run_async(self, coro):
        """Запуск корутины в асинхронном цикле"""
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    # Остальные методы остаются без изменений, но с заменой self.root на self
    def create_main_menu(self):
        self.clear_window()
        ttk.Button(
            self,
            text="Подключиться к серверу",
            command=lambda: self.run_async(self.connect_to_server())
        ).pack(pady=20)

    def create_control_panel(self):
        self.clear_window()
        ttk.Label(self, text=f"Ваш ID: {self.client_id}",
                  font=('Helvetica', 12, 'bold')).pack(pady=10)

        buttons = [
            ("Список участников", self.show_clients),
            ("Синхронизировать всех", self.sync_all_window),
            ("Клик конкретному", self.single_client_window)
        ]

        for text, cmd in buttons:
            ttk.Button(self, text=text, command=cmd).pack(pady=5)

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
    def start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def connect_to_server(self):
        try:
            self.websocket = await websockets.connect("ws://64.227.113.220:8765")
            message = await self.websocket.recv()
            data = json.loads(message)

            if data["type"] == "client_id":
                self.client_id = data["id"]
                # Используем self вместо self.root
                self.after(0, self.create_control_panel)
                asyncio.create_task(self.listen_messages())
                asyncio.create_task(self.send_ping())

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", str(e)))

    async def send_ping(self):
        while True:
            if self.websocket:
                try:
                    await self.websocket.send(json.dumps({
                        "type": "ping",
                        "client_time": time.time()
                    }))
                except:
                    pass
            await asyncio.sleep(5)

    async def listen_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)

                if data["type"] == "client_list":
                    # Создаем структуру с ping=0 для новых клиентов
                    self.clients_data = {
                        client_id: {"ping": self.clients_data.get(client_id, {}).get("ping", 0)}
                        for client_id in data["clients"]
                    }
                    self.after(0, self.update_clients_list)

                elif data["type"] == "pong":
                    # Обновляем только значения ping
                    for client_id, ping_value in data["clients"].items():
                        if client_id in self.clients_data:
                            self.clients_data[client_id]["ping"] = ping_value
                        else:
                            self.clients_data[client_id] = {"ping": ping_value}
                    self.after(0, self.update_clients_list)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", str(e)))

    def show_clients(self):
        self.clients_window = tk.Toplevel(self)  # Заменили self.root на self
        self.clients_window.title("Список участников")

        self.tree = ttk.Treeview(self.clients_window, columns=("ID", "Ping"), show="headings")
        self.tree.heading("ID", text="ID клиента")
        self.tree.heading("Ping", text="Ping (мс)")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.update_clients_list()

        ttk.Button(self.clients_window, text="Обновить",
                   command=lambda: self.run_async(self.request_clients_list())).pack(pady=5)

        ttk.Button(self.clients_window, text="Копировать ID",
                   command=self.copy_selected_id).pack(pady=5)

    def update_clients_list(self):
        if hasattr(self, 'tree'):
            self.tree.delete(*self.tree.get_children())
            for client_id, data in self.clients_data.items():
                ping = data.get("ping", 0)
                self.tree.insert("", "end", values=(client_id, f"{ping:.1f} мс"))

    def copy_selected_id(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            pyperclip.copy(item['values'][0])
            messagebox.showinfo("Успешно", "ID скопирован в буфер обмена")

    def sync_all_window(self):
        window = tk.Toplevel(self)  # Исправлено
        window.title("Синхронизация кликов")

        ttk.Label(window, text="Задержка (секунды):").grid(row=0, column=0)
        delay_entry = ttk.Entry(window)
        delay_entry.grid(row=0, column=1)

        ttk.Label(window, text="X (% экрана):").grid(row=1, column=0)
        x_entry = ttk.Entry(window)
        x_entry.grid(row=1, column=1)

        ttk.Label(window, text="Y (% экрана):").grid(row=2, column=0)
        y_entry = ttk.Entry(window)
        y_entry.grid(row=2, column=1)

        def send_command():
            asyncio.run_coroutine_threadsafe(
                self.send_click_command(
                    "all",
                    float(x_entry.get()),
                    float(y_entry.get()),
                    float(delay_entry.get())
                ),
                self.loop
            )
            window.destroy()

        ttk.Button(window, text="Отправить", command=send_command).grid(row=3, columnspan=2)

    def single_client_window(self):
        window = tk.Toplevel(self)
        window.title("Клик конкретному клиенту")

        # Функция для вставки с учетом выделенного текста
        def paste_id(event=None):
            try:
                text = pyperclip.paste()
                if text:
                    # Удаляем выделенный текст и вставляем из буфера
                    client_entry.delete("sel.first", "sel.last")
                    client_entry.insert("insert", text)
            except Exception as e:
                print(f"Ошибка вставки: {e}")

        ttk.Label(window, text="ID клиента:").grid(row=0, column=0)
        client_entry = ttk.Entry(window)
        client_entry.grid(row=0, column=1, padx=5, pady=5)

        # Универсальные горячие клавиши для разных ОС
        client_entry.bind("<Control-v>", paste_id)  # Windows/Linux
        client_entry.bind("<Command-v>", paste_id)  # macOS

        menu = tk.Menu(window, tearoff=0)
        menu.add_command(label="Вставить", command=paste_id)

        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)

        client_entry.bind("<Button-3>", show_menu)  # Правая кнопка мыши

        ttk.Label(window, text="X (% экрана):").grid(row=1, column=0)
        x_entry = ttk.Entry(window)
        x_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(window, text="Y (% экрана):").grid(row=2, column=0)
        y_entry = ttk.Entry(window)
        y_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(window, text="Задержка (секунды):").grid(row=3, column=0)
        delay_entry = ttk.Entry(window)
        delay_entry.grid(row=3, column=1, padx=5, pady=5)

        def send_command():
            asyncio.run_coroutine_threadsafe(
                self.send_click_command(
                    [client_entry.get()],
                    float(x_entry.get()),
                    float(y_entry.get()),
                    float(delay_entry.get())
                ),
                self.loop
            )
            window.destroy()

        ttk.Button(window, text="Отправить", command=send_command).grid(row=4, columnspan=2, pady=10)

    async def send_click_command(self, targets, x_percent, y_percent, delay):
        try:
            await self.websocket.send(json.dumps({
                "type": "command",
                "targets": targets,
                "command": {
                    "type": "click",
                    "percent_x": x_percent,
                    "percent_y": y_percent,
                    "time": time.time() + delay
                }
            }))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", str(e)))  # Исправлено
    async def request_clients_list(self):
        await self.websocket.send(json.dumps({"type": "showclients"}))


if __name__ == "__main__":
    app = ClickControlApp()
    app.mainloop()
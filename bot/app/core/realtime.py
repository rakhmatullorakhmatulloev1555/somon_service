class Manager:

    def __init__(self):
        self.clients = []

    async def connect(self, ws):
        await ws.accept()
        self.clients.append(ws)

    def disconnect(self, ws):
        self.clients.remove(ws)

    async def broadcast(self, data):
        for c in self.clients:
            await c.send_json(data)

manager = Manager()

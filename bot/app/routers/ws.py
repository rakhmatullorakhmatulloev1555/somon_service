from fastapi import APIRouter, WebSocket

router = APIRouter()

clients = []

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):

    await ws.accept()

    clients.append(ws)

    try:
        while True:
            await ws.receive_text()
    except:
        clients.remove(ws)


async def broadcast(data):

    for c in clients:
        await c.send_json(data)
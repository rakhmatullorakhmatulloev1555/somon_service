from fastapi import APIRouter, WebSocket
import app.bot.services.ticket_service as ticket_service
import asyncio

router = APIRouter()

connections = []

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):

    await ws.accept()
    connections.append(ws)

    while True:

        tickets = ticket_service.get_all_tickets()

        await ws.send_json(tickets)

        await asyncio.sleep(2)

# app/bot/tasks/notifications.py
import asyncio
from aiogram import Bot
from app.services import event_service
from datetime import datetime

async def check_event_notifications(bot: Bot):
    """Проверка и отправка уведомлений о событиях"""
    while True:
        try:
            events = event_service.get_events_for_notification()
            
            for event in events:
                if event.master and event.master.telegram_id:
                    time_until = event.start_date - datetime.now()
                    minutes = int(time_until.total_seconds() / 60)
                    
                    text = f"""
⏰ <b>НАПОМИНАНИЕ О СОБЫТИИ</b>

📌 {event.title}
🕐 Через {minutes} минут
📅 {event.start_date.strftime('%d.%m.%Y %H:%M')}

{event.description or ''}
"""
                    await bot.send_message(
                        chat_id=int(event.master.telegram_id),
                        text=text,
                        parse_mode="HTML"
                    )
                    
                    # Отмечаем, что уведомление отправлено
                    event_service.update_event(event.id, {"notification_sent": True})
        
        except Exception as e:
            print(f"Error in notification task: {e}")
        
        await asyncio.sleep(60)  # Проверяем каждую минуту

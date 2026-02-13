# app/bot/handlers/master.py
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text

from app.models.master import Master
from app.models.ticket import Ticket
from app.models.client import Client
from app.database import SessionLocal
from app.bot.data.masters import MASTERS
from app.bot.config import ADMIN_IDS, MASTER_GROUP_ID
import app.bot.services.ticket_service as ticket_service
import logging

from .common import (
    build_master_keyboard, build_master_select_keyboard,
    get_or_create_master
)

logger = logging.getLogger(__name__)

def register_master_handlers(dp: Dispatcher):
    
    # ---------- MASTER FLOW ----------
    @dp.callback_query_handler(Text(startswith="assign_"))
    async def assign_master(callback: types.CallbackQuery):
        """Отправить заявку в группу мастеров для назначения"""
        ticket_id = int(callback.data.split("_")[1])
        await callback.bot.send_message(
            MASTER_GROUP_ID,
            f"📢 Новая заявка #{ticket_id}\nВыберите мастера:",
            reply_markup=build_master_select_keyboard(ticket_id)
        )
        await callback.answer("Отправлено в группу мастеров")

    @dp.callback_query_handler(Text(startswith="take:"))
    async def master_take(callback: types.CallbackQuery):
        """Назначение мастера на заявку (только для админов)"""
        try:
            _, ticket_id, master_telegram_id = callback.data.split(":")
            ticket_id = int(ticket_id)
            master_telegram_id = int(master_telegram_id)

            logger.info(f"Назначение мастера. Ticket: {ticket_id}, Master Telegram ID: {master_telegram_id}")

            # Получаем заявку
            ticket = ticket_service.get_ticket(ticket_id)

            if not ticket:
                await callback.answer("❌ Заявка не найдена", show_alert=True)
                return

            # 🔒 ТОЛЬКО АДМИН МОЖЕТ НАЗНАЧАТЬ
            if callback.from_user.id not in ADMIN_IDS:
                await callback.answer("⛔ Только администратор может назначать мастера", show_alert=True)
                return

            # Ищем мастера в списке MASTERS
            master_info = None
            for m in MASTERS:
                if str(m.get('telegram_id')) == str(master_telegram_id):
                    master_info = m
                    logger.info(f"Найден мастер в MASTERS: {m['name']}")
                    break

            if not master_info:
                logger.error(f"Мастер с telegram_id {master_telegram_id} не найден в MASTERS")
                await callback.answer("❌ Мастер не найден", show_alert=True)
                return

            # Находим или создаем мастера
            master = get_or_create_master(master_info)
            if not master:
                await callback.answer("❌ Ошибка при создании мастера", show_alert=True)
                return

            logger.info(f"Мастер создан/найден. ID: {master.id}, Telegram ID: {master.telegram_id}")

            # Назначаем мастера на заявку через ticket_service
            success, message = ticket_service.assign_master_by_telegram(ticket_id, master_telegram_id)
            if not success:
                logger.error(f"Ошибка при назначении мастера на заявку: {message}")
                await callback.answer(f"❌ {message}", show_alert=True)
                return

            logger.info(f"Мастер {master.id} назначен на заявку {ticket_id}")

            # Уведомление мастеру
            try:
                await callback.bot.send_message(
                    master_telegram_id,
                    f"🛠 Вам назначена заявка #{ticket_id}\n"
                    f"📱 Устройство: {ticket.brand}\n"
                    f"🔧 Проблема: {ticket.problem[:100]}...",
                    reply_markup=build_master_keyboard(ticket_id)
                )
                logger.info(f"Уведомление отправлено мастеру {master_telegram_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления мастеру: {e}")

            # Уведомление клиенту
            client_telegram_id = None
            if ticket.client and ticket.client.telegram_id:
                client_telegram_id = ticket.client.telegram_id
            
            if client_telegram_id:
                try:
                    await callback.bot.send_message(
                        client_telegram_id,
                        f"✅ Ваша заявка #{ticket_id} взята в работу мастером {master.name}"
                    )
                    logger.info(f"Уведомление отправлено клиенту {client_telegram_id}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления клиенту: {e}")

            # Скрываем список мастеров в группе
            await callback.message.edit_text(
                f"✅ Заявка #{ticket_id} назначена мастеру {master.name}"
            )

            await callback.answer("Мастер назначен")

        except Exception as e:
            logger.error(f"Ошибка в master_take: {e}", exc_info=True)
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    @dp.callback_query_handler(Text(startswith="status_"))
    async def update_status(callback: types.CallbackQuery):
        """Обновление статуса заявки мастером"""
        try:
            _, status, ticket_id = callback.data.split("_")
            ticket_id = int(ticket_id)

            status_map = {
                "diag": "🧪 Диагностика",
                "repair": "🔧 В ремонте",
                "done": "✅ Готово"
            }

            # Получаем заявку
            ticket = ticket_service.get_ticket(ticket_id)

            if not ticket:
                await callback.answer("❌ Заявка не найдена", show_alert=True)
                return
        
            new_status = status_map.get(status)
            if not new_status:
                await callback.answer("❌ Неверный статус", show_alert=True)
                return

            # ПРОСТОЙ ВАРИАНТ - разрешаем любой статус без проверок
            success = ticket_service.update_status(ticket_id, new_status)
            if not success:
                await callback.answer("❌ Ошибка при обновлении статуса", show_alert=True)
                return

            # Уведомление клиенту о статусе
            client_telegram_id = None
            if ticket.client and ticket.client.telegram_id:
                client_telegram_id = ticket.client.telegram_id
            
            if client_telegram_id:
                try:
                    await callback.bot.send_message(
                        client_telegram_id,
                        f"📢 Статус вашей заявки #{ticket_id} обновлён:\n{new_status}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления клиенту: {e}")

            # Если статус "Готово" → отправляем рейтинг
            if status == "done" and client_telegram_id:
                # Получаем master_id из заявки
                master_id = ticket.master_id
                
                if master_id:
                    from app.bot.keyboards.rating import rating_keyboard

                    try:
                        await callback.bot.send_message(
                            client_telegram_id,
                            "⭐ Оцените работу мастера:",
                            reply_markup=rating_keyboard(master_id)
                        )
                        logger.info(f"Отзыв отправлен клиенту {client_telegram_id} для мастера {master_id}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке запроса на оценку: {e}")
                else:
                    logger.warning(f"Не удалось отправить отзыв. master_id не найден в заявке {ticket_id}")

            # Обновляем сообщение мастеру
            await callback.message.edit_text(
                f"📌 Заявка #{ticket_id}\nСтатус: {new_status}",
                reply_markup=build_master_keyboard(ticket_id, new_status)
            )

            await callback.answer("Статус обновлён")
            
        except Exception as e:
            logger.error(f"Ошибка в update_status: {e}", exc_info=True)
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    @dp.callback_query_handler(lambda c: c.data.startswith("rate_"))
    async def rate_master(callback: types.CallbackQuery):
        """Оценка работы мастера клиентом"""
        try:
            _, master_id_str, rating_str = callback.data.split("_")
            master_id = int(master_id_str)
            rating = int(rating_str)
            
            # Сразу отвечаем на callback, чтобы избежать InvalidQueryID
            try:
                await callback.answer()
            except:
                pass
            
            db = SessionLocal()
            master = db.query(Master).get(master_id)
            
            if not master:
                try:
                    await callback.answer("❌ Мастер не найден", show_alert=True)
                except:
                    pass
                db.close()
                return
            
            # Сохраняем старый рейтинг для отчета
            old_rating = master.rating
            old_count = master.rating_count
            
            # Рассчитываем новый рейтинг
            if master.rating_count > 0:
                master.rating = (
                    (master.rating * master.rating_count + rating)
                    / (master.rating_count + 1)
                )
            else:
                master.rating = rating
            
            master.rating_count += 1
            
            db.commit()
            
            # Уведомление мастеру о новом отзыве
            if master.telegram_id:
                rating_emoji = "⭐" * rating
                try:
                    await callback.bot.send_message(
                        master.telegram_id,
                        f"""
🎉 Новый отзыв!

⭐ Вам поставили оценку: {rating_emoji} ({rating}/5)

📈 Ваш рейтинг обновлен:
  Было: {old_rating:.2f} ({old_count} оценок)
  Стало: {master.rating:.2f} ({master.rating_count} оценок)

Спасибо за качественную работу! 💪
"""
                    )
                    logger.info(f"Уведомление отправлено мастеру {master.telegram_id}")
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление мастеру: {e}")
            
            # Уведомление админам
            rating_emoji = "⭐" * rating
            
            admin_message = f"""
📊 Новый отзыв для мастера:

👤 Мастер: {master.name} {master.surname or ''}
🏷 Специализация: {master.specialization}
⭐ Оценка: {rating_emoji} ({rating}/5)

📈 Рейтинг обновлен:
  Было: {old_rating:.2f} ({old_count} оценок)
  Стало: {master.rating:.2f} ({master.rating_count} оценок)
"""
            
            # Отправляем всем админам
            for admin_id in ADMIN_IDS:
                try:
                    await callback.bot.send_message(
                        admin_id,
                        admin_message
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
            
            db.close()
            
            # Обновляем сообщение
            try:
                await callback.message.edit_text(
                    "Спасибо за отзыв ⭐\n\n"
                    f"Ваша оценка: {rating_emoji} ({rating}/5)\n"
                    f"Мастер: {master.name}\n\n"
                    "Ваш отзыв помогает нам стать лучше! 🙏"
                )
            except Exception as e:
                logger.warning(f"Не удалось обновить сообщение: {e}")
                
        except Exception as e:
            logger.error(f"Ошибка в rate_master: {e}", exc_info=True)
            try:
                await callback.answer("❌ Произошла ошибка", show_alert=True)
            except:
                pass

    # ---------- HELPERS ----------
    @dp.message_handler(commands=['mytickets'])
    async def show_my_tickets(message: types.Message):
        """Показать заявки мастера"""
        db = SessionLocal()
        try:
            # Находим мастера по Telegram ID
            master = db.query(Master).filter(
                Master.telegram_id == str(message.from_user.id)
            ).first()
            
            if not master:
                await message.answer("❌ Вы не зарегистрированы как мастер")
                return
            
            # Получаем заявки мастера
            tickets = db.query(Ticket).filter(
                Ticket.master_id == master.id
            ).order_by(Ticket.created_at.desc()).all()
            
            if not tickets:
                await message.answer("📭 У вас нет назначенных заявок")
                return
            
            text = f"📋 <b>Ваши заявки ({len(tickets)}):</b>\n\n"
            
            for i, ticket in enumerate(tickets, 1):
                status_emoji = {
                    "Новая": "🆕",
                    "🧪 Диагностика": "🔍",
                    "🔧 В ремонте": "🛠️",
                    "✅ Готово": "✅",
                    "В работе": "⚙️"
                }.get(ticket.status, "📝")
                
                text += f"{i}. {status_emoji} <b>#{ticket.id}</b> - {ticket.status}\n"
                text += f"   📱 {ticket.brand}\n"
                text += f"   🔧 {ticket.problem[:50]}...\n"
                text += f"   📅 {ticket.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            await message.answer(text, parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Ошибка при получении заявок мастера: {e}")
            await message.answer("❌ Произошла ошибка при получении заявок")
        finally:
            db.close()

    @dp.message_handler(commands=['myrating'])
    async def show_my_rating(message: types.Message):
        """Показать рейтинг мастера"""
        db = SessionLocal()
        try:
            master = db.query(Master).filter(
                Master.telegram_id == str(message.from_user.id)
            ).first()
            
            if not master:
                await message.answer("❌ Вы не зарегистрированы как мастер")
                return
            
            rating_stars = "⭐" * int(master.rating) if master.rating > 0 else "Нет оценок"
            
            text = f"""
📊 <b>ВАШ РЕЙТИНГ</b>

👤 Мастер: {master.name} {master.surname or ''}
🏷 Специализация: {master.specialization or 'Не указана'}
⭐ Рейтинг: {master.rating:.2f} {rating_stars}
📊 Количество оценок: {master.rating_count}
✅ Выполнено заявок: {master.completed_orders or 0}
🔧 В работе: {master.active_orders or 0}
"""
            
            await message.answer(text, parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Ошибка при получении рейтинга мастера: {e}")
            await message.answer("❌ Произошла ошибка")
        finally:
            db.close()
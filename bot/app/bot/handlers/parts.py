# app/bot/handlers/parts.py
import asyncio
import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import logging

from app.database import SessionLocal
from app.models.part import Part, PartCategory, PartSupplier
from app.services import part_service
from app.bot.config import ADMIN_IDS

logger = logging.getLogger(__name__)

# ============================================
# СОСТОЯНИЯ ДЛЯ ДОБАВЛЕНИЯ ЗАПЧАСТЕЙ
# ============================================

class PartStates(StatesGroup):
    # Для категорий
    waiting_category_name = State()
    waiting_category_description = State()
    
    # Для поставщиков
    waiting_supplier_name = State()
    waiting_supplier_contact = State()
    waiting_supplier_phone = State()
    waiting_supplier_email = State()
    waiting_supplier_address = State()
    
    # Для запчастей
    waiting_part_name = State()
    waiting_part_sku = State()
    waiting_part_category = State()
    waiting_part_brand = State()
    waiting_part_purchase_price = State()
    waiting_part_sale_price = State()
    waiting_part_stock = State()
    waiting_part_min_stock = State()
    waiting_part_supplier = State()
    waiting_part_description = State()
    waiting_part_location = State()
    
    # Для пополнения запаса
    waiting_restock_quantity = State()
    waiting_restock_notes = State()

# ============================================
# ПРОВЕРКА ПРАВ АДМИНА
# ============================================

def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

# ============================================
# ГЛАВНОЕ МЕНЮ ЗАПЧАСТЕЙ
# ============================================

async def cmd_parts(callback: types.CallbackQuery):
    """Главное меню управления запчастями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📦 Все запчасти", callback_data="parts_list"),
        InlineKeyboardButton("➕ Добавить запчасть", callback_data="parts_add")
    )
    keyboard.add(
        InlineKeyboardButton("⚠️ Низкий запас", callback_data="parts_low_stock"),
        InlineKeyboardButton("📊 Статистика", callback_data="parts_stats")
    )
    keyboard.add(
        InlineKeyboardButton("🏷️ Категории", callback_data="parts_categories_menu"),
        InlineKeyboardButton("🚚 Поставщики", callback_data="parts_suppliers_menu")
    )
    keyboard.add(
        InlineKeyboardButton("🔍 Поиск", callback_data="parts_search")
    )
    keyboard.add(
        InlineKeyboardButton("◀️ НАЗАД В АДМИНКУ", callback_data="admin_menu")
    )
    
    await callback.message.edit_text(  # ✅ ПРАВИЛЬНО: edit_text для callback
        "🔧 <b>УПРАВЛЕНИЕ СКЛАДОМ ЗАПЧАСТЕЙ</b>\n\n"
        "Выберите действие:\n\n"
        "📦 <b>Все запчасти</b> - просмотр всего склада\n"
        "➕ <b>Добавить запчасть</b> - новая позиция\n"
        "⚠️ <b>Низкий запас</b> - требуется пополнение\n"
        "📊 <b>Статистика</b> - анализ склада\n"
        "🏷️ <b>Категории</b> - управление категориями\n"
        "🚚 <b>Поставщики</b> - управление поставщиками\n"
        "🔍 <b>Поиск</b> - поиск по артикулу/названию",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ============================================
# ПРОСМОТР ВСЕХ ЗАПЧАСТЕЙ
# ============================================

async def parts_list_callback(callback: types.CallbackQuery):
    """Показать список всех запчастей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    parts = part_service.get_all_parts()
    
    if not parts:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("➕ Добавить запчасть", callback_data="parts_add"))
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="parts_menu"))
        
        await callback.message.edit_text(
            "📦 На складе нет запчастей\n\n"
            "Нажмите кнопку ниже, чтобы добавить первую запчасть!",
            reply_markup=keyboard
        )
        return
    
    # Показываем первые 10 запчастей
    text = "📦 <b>СПИСОК ЗАПЧАСТЕЙ</b>\n\n"
    
    for i, part in enumerate(parts[:10], 1):
        status_emoji = {
            "high": "✅",
            "medium": "⚡",
            "low": "⚠️",
            "out": "❌"
        }.get(part["status"], "📦")
        
        text += f"{status_emoji} <b>{part['name']}</b>\n"
        text += f"   📋 Артикул: <code>{part['sku']}</code>\n"
        text += f"   📦 В наличии: {part['stock']} шт.\n"
        text += f"   💰 Цена: {part['sale_price']} сомони\n"
        text += f"   🏷️ Категория: {part['category_name']}\n"
        text += "─" * 20 + "\n"
    
    if len(parts) > 10:
        text += f"\n... и еще {len(parts) - 10} запчастей\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить", callback_data="parts_add"),
        InlineKeyboardButton("🔍 Поиск", callback_data="parts_search")
    )
    keyboard.add(
        InlineKeyboardButton("⚠️ Низкий запас", callback_data="parts_low_stock"),
        InlineKeyboardButton("◀️ Назад", callback_data="parts_menu")
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# ============================================
# ЗАПЧАСТИ С НИЗКИМ ЗАПАСОМ
# ============================================

async def parts_low_stock_callback(callback: types.CallbackQuery):
    """Показать запчасти с низким запасом"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    low_stock = part_service.get_low_stock_parts()
    
    if not low_stock:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="parts_menu"))
        
        await callback.message.edit_text(
            "✅ Нет запчастей с низким запасом!\n\n"
            "Все позиции в норме.",
            reply_markup=keyboard
        )
        return
    
    text = "⚠️ <b>ЗАПЧАСТИ С НИЗКИМ ЗАПАСОМ</b>\n\n"
    
    for part in low_stock:
        text += f"🔴 <b>{part['name']}</b>\n"
        text += f"   📋 Артикул: <code>{part['sku']}</code>\n"
        text += f"   📦 В наличии: {part['stock']} шт.\n"
        text += f"   ⚠️ Минимум: {part['min_stock']} шт.\n"
        text += f"   🏷️ Категория: {part['category_name']}\n"
        text += "─" * 20 + "\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Пополнить", callback_data="parts_restock_menu"),
        InlineKeyboardButton("🔄 Обновить", callback_data="parts_low_stock")
    )
    keyboard.add(
        InlineKeyboardButton("◀️ Назад", callback_data="parts_menu")
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# ============================================
# СТАТИСТИКА СКЛАДА
# ============================================

async def parts_stats_callback(callback: types.CallbackQuery):
    """Показать статистику склада"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    stats = part_service.get_part_statistics()
    
    text = f"""
📊 <b>СТАТИСТИКА СКЛАДА</b>

📦 <b>ОБЩАЯ ИНФОРМАЦИЯ:</b>
• Всего наименований: {stats['total_parts']}
• Категорий: {stats['total_categories']}
• Поставщиков: {stats['total_suppliers']}
• С низким запасом: {stats['low_stock']}

💰 <b>ФИНАНСЫ:</b>
• Закупочная стоимость: {stats['total_value']:,.0f} сомони
• Продажная стоимость: {stats['total_sale_value']:,.0f} сомони
• Потенциальная прибыль: {stats['potential_profit']:,.0f} сомони

🏷️ <b>КАТЕГОРИИ:</b>
"""
    
    for cat in stats['categories'][:5]:
        text += f"• {cat['name']}: {cat['parts_count']} шт. ({cat['total_value']:,.0f} сомони)\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔄 Обновить", callback_data="parts_stats"))
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="parts_menu"))
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# ============================================
# ДОБАВЛЕНИЕ НОВОЙ ЗАПЧАСТИ
# ============================================

async def parts_add_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало добавления новой запчасти"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    await state.finish()
    
    await callback.message.edit_text(
        "➕ <b>ДОБАВЛЕНИЕ НОВОЙ ЗАПЧАСТИ</b>\n\n"
        "Шаг 1/8: Введите <b>название</b> запчасти\n\n"
        "Пример: <i>Экран iPhone 12</i>",
        parse_mode="HTML"
    )
    await PartStates.waiting_part_name.set()

async def process_part_name(message: types.Message, state: FSMContext):
    """Обработка названия запчасти"""
    if len(message.text.strip()) < 3:
        await message.answer("⚠️ Название слишком короткое. Введите минимум 3 символа:")
        return
    
    await state.update_data(name=message.text.strip())
    
    await message.answer(
        "Шаг 2/8: Введите <b>артикул</b> (SKU)\n\n"
        "Артикул должен быть уникальным!\n"
        "Пример: <code>IP12-SCR-001</code>",
        parse_mode="HTML"
    )
    await PartStates.waiting_part_sku.set()

async def process_part_sku(message: types.Message, state: FSMContext):
    """Обработка артикула запчасти"""
    sku = message.text.strip().upper()
    
    if len(sku) < 3:
        await message.answer("⚠️ Артикул слишком короткий. Введите минимум 3 символа:")
        return
    
    # Проверяем уникальность SKU
    db = SessionLocal()
    existing = db.query(Part).filter(Part.sku == sku).first()
    db.close()
    
    if existing:
        await message.answer(
            f"❌ Запчасть с артикулом <code>{sku}</code> уже существует!\n\n"
            "Введите другой артикул:",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(sku=sku)
    
    # Получаем список категорий
    categories = part_service.get_all_categories()
    
    if not categories:
        # Если категорий нет, предлагаем создать
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("➕ Создать категорию", callback_data="parts_category_add"))
        keyboard.add(InlineKeyboardButton("◀️ Отмена", callback_data="parts_menu"))
        
        await message.answer(
            "❌ В системе нет категорий!\n\n"
            "Сначала создайте категорию для запчасти.",
            reply_markup=keyboard
        )
        await state.finish()
        return
    
    # Создаем клавиатуру с категориями
    keyboard = InlineKeyboardMarkup(row_width=1)
    for cat in categories[:10]:
        keyboard.add(InlineKeyboardButton(
            f"{cat['name']} ({cat['count']} шт.)",
            callback_data=f"part_cat_{cat['id']}"
        ))
    
    await message.answer(
        "Шаг 3/8: Выберите <b>категорию</b> запчасти:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await PartStates.waiting_part_category.set()

async def part_category_callback(callback: types.CallbackQuery, state: FSMContext):
    """Выбор категории запчасти"""
    await callback.answer()
    
    category_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=category_id)
    
    # Получаем название категории
    categories = part_service.get_all_categories()
    category_name = next((c['name'] for c in categories if c['id'] == category_id), "Неизвестно")
    
    await callback.message.edit_text(
        f"✅ Выбрана категория: <b>{category_name}</b>\n\n"
        "Шаг 4/8: Введите <b>бренд</b> запчасти\n"
        "Если бренда нет, отправьте прочерк: <code>-</code>",
        parse_mode="HTML"
    )
    await PartStates.waiting_part_brand.set()

async def process_part_brand(message: types.Message, state: FSMContext):
    """Обработка бренда запчасти"""
    brand = message.text.strip()
    if brand == "-":
        brand = None
    
    await state.update_data(brand=brand)
    
    await message.answer(
        "Шаг 5/8: Введите <b>закупочную цену</b> (в сомони)\n\n"
        "Пример: <code>180.50</code>",
        parse_mode="HTML"
    )
    await PartStates.waiting_part_purchase_price.set()

async def process_part_purchase_price(message: types.Message, state: FSMContext):
    """Обработка закупочной цены"""
    try:
        price = float(message.text.strip().replace(",", "."))
        if price < 0:
            raise ValueError
    except:
        await message.answer("⚠️ Введите корректную цену (положительное число):")
        return
    
    await state.update_data(purchase_price=price)
    
    await message.answer(
        "Шаг 6/8: Введите <b>продажную цену</b> (в сомони)\n\n"
        "Пример: <code>350.00</code>",
        parse_mode="HTML"
    )
    await PartStates.waiting_part_sale_price.set()

async def process_part_sale_price(message: types.Message, state: FSMContext):
    """Обработка продажной цены"""
    try:
        price = float(message.text.strip().replace(",", "."))
        if price < 0:
            raise ValueError
    except:
        await message.answer("⚠️ Введите корректную цену (положительное число):")
        return
    
    await state.update_data(sale_price=price)
    
    await message.answer(
        "Шаг 7/8: Введите <b>количество</b> на складе\n\n"
        "Пример: <code>10</code>",
        parse_mode="HTML"
    )
    await PartStates.waiting_part_stock.set()

async def process_part_stock(message: types.Message, state: FSMContext):
    """Обработка количества на складе"""
    try:
        stock = int(message.text.strip())
        if stock < 0:
            raise ValueError
    except:
        await message.answer("⚠️ Введите корректное количество (целое положительное число):")
        return
    
    await state.update_data(stock=stock)
    
    await message.answer(
        "Шаг 8/8: Введите <b>минимальный запас</b>\n\n"
        "При достижении этого количества будет отображаться предупреждение.\n"
        "По умолчанию: <code>5</code>",
        parse_mode="HTML"
    )
    await PartStates.waiting_part_min_stock.set()

async def process_part_min_stock(message: types.Message, state: FSMContext):
    """Обработка минимального запаса и создание запчасти"""
    try:
        min_stock = int(message.text.strip())
        if min_stock < 0:
            raise ValueError
    except:
        await message.answer("⚠️ Введите корректное значение (целое положительное число):")
        return
    
    await state.update_data(min_stock=min_stock)
    
    # Получаем данные
    data = await state.get_data()
    
    # Создаем запчасть
    try:
        part_data = {
            "name": data["name"],
            "sku": data["sku"],
            "category_id": data["category_id"],
            "brand": data.get("brand"),
            "purchase_price": data["purchase_price"],
            "sale_price": data["sale_price"],
            "stock": data["stock"],
            "min_stock": data["min_stock"]
        }
        
        # Создаем запчасть через сервис
        part = part_service.create_part(part_data)
        
        # Получаем все категории для отображения названия
        categories = part_service.get_all_categories()
        
        # Получаем название категории
        category_name = "Неизвестно"
        for cat in categories:
            if cat['id'] == part.category_id:
                category_name = cat['name']
                break
        
        # Формируем текст без HTML-тегов в названиях
        status_text = {
            "high": "✅ Высокий",
            "medium": "⚡ Средний", 
            "low": "⚠️ Низкий",
            "out": "❌ Нет в наличии"
        }.get(part.status, "📦 В наличии")
        
        success_text = f"""✅ ЗАПЧАСТЬ УСПЕШНО ДОБАВЛЕНА!

📦 Наименование: {part.name}
📋 Артикул: {part.sku}
🏷️ Категория: {category_name}
🏭 Бренд: {part.brand or 'Не указан'}

💰 ЦЕНЫ:
• Закупка: {part.purchase_price} сомони
• Продажа: {part.sale_price} сомони
• Прибыль: {part.sale_price - part.purchase_price} сомони

📊 СКЛАД:
• В наличии: {part.stock} шт.
• Минимум: {part.min_stock} шт.
• Статус: {status_text}"""
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ Еще запчасть", callback_data="parts_add"),
            InlineKeyboardButton("📦 Все запчасти", callback_data="parts_list")
        )
        keyboard.add(
            InlineKeyboardButton("◀️ В меню", callback_data="parts_menu")
        )
        
        await message.answer(success_text, reply_markup=keyboard)
        
    except ValueError as e:
        logger.error(f"Ошибка при создании запчасти: {e}")
        await message.answer(f"❌ Ошибка при создании запчасти: проверьте правильность введенных данных")
    except Exception as e:
        logger.error(f"Ошибка при создании запчасти: {e}")
        
        # Проверяем, может быть такая запчасть уже существует
        if "already exists" in str(e).lower() or "уже существует" in str(e).lower():
            error_text = f"❌ Запчасть с артикулом {data.get('sku', '')} уже существует!"
        else:
            error_text = f"❌ Ошибка при создании запчасти. Попробуйте позже."
        
        await message.answer(error_text)
    
    await state.finish()

def get_status_text(status):
    """Получить текстовое описание статуса"""
    status_map = {
        "high": "✅ Высокий",
        "medium": "⚡ Средний",
        "low": "⚠️ Низкий",
        "out": "❌ Нет в наличии"
    }
    return status_map.get(status, status)

# ============================================
# УПРАВЛЕНИЕ КАТЕГОРИЯМИ (ЕДИНСТВЕННАЯ ВЕРСИЯ)
# ============================================

async def parts_categories_menu_callback(callback: types.CallbackQuery):
    """Меню управления категориями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    categories = part_service.get_all_categories()
    
    text = "🏷️ <b>УПРАВЛЕНИЕ КАТЕГОРИЯМИ</b>\n\n"
    
    if categories:
        for cat in categories:
            text += f"• <b>{cat['name']}</b> - {cat['count']} запчастей\n"
            if cat.get('description'):
                text += f"  <i>{cat['description']}</i>\n"
    else:
        text += "Нет созданных категорий\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Создать категорию", callback_data="parts_category_add"),
        InlineKeyboardButton("🗑 Удалить категорию", callback_data="parts_category_delete_list")
    )
    keyboard.add(
        InlineKeyboardButton("◀️ Назад", callback_data="parts_menu"),
        InlineKeyboardButton("◀️ В АДМИНКУ", callback_data="admin_menu")
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

async def parts_category_add_callback(callback: types.CallbackQuery, state: FSMContext):
    """Добавление новой категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    await state.finish()
    
    await callback.message.edit_text(
        "➕ <b>СОЗДАНИЕ НОВОЙ КАТЕГОРИИ</b>\n\n"
        "Введите название категории:\n"
        "Пример: <i>Экраны</i>",
        parse_mode="HTML"
    )
    await PartStates.waiting_category_name.set()

async def process_category_name(message: types.Message, state: FSMContext):
    """Обработка названия категории"""
    if len(message.text.strip()) < 2:
        await message.answer("⚠️ Название слишком короткое. Введите минимум 2 символа:")
        return
    
    await state.update_data(category_name=message.text.strip())
    
    await message.answer(
        "Введите описание категории (или отправьте '-' если не нужно):\n"
        "Пример: <i>Дисплеи и сенсорные стекла</i>",
        parse_mode="HTML"
    )
    await PartStates.waiting_category_description.set()

async def process_category_description(message: types.Message, state: FSMContext):
    """Обработка описания категории"""
    data = await state.get_data()
    
    description = message.text.strip()
    if description == "-":
        description = None
    
    try:
        # Проверяем, не существует ли уже такая категория
        categories = part_service.get_all_categories()
        for cat in categories:
            if cat['name'].lower() == data["category_name"].lower():
                await message.answer(
                    f"❌ Категория '{data['category_name']}' уже существует!\n\n"
                    "Введите другое название:"
                )
                await PartStates.waiting_category_name.set()
                return
        
        category = part_service.create_category({
            "name": data["category_name"],
            "description": description,
            "icon": "fas fa-box"
        })
        
        await message.answer(
            f"✅ Категория <b>{category.name}</b> успешно создана!",
            parse_mode="HTML"
        )
        
        # Возвращаемся в меню категорий
        await parts_categories_menu_callback(
            types.CallbackQuery(
                id="0",
                from_user=message.from_user,
                message=message,
                data="parts_categories_menu",
                chat_instance="0"
            )
        )
        
    except Exception as e:
        logger.error(f"Ошибка при создании категории: {e}")
        await message.answer(f"❌ Ошибка при создании категории: {str(e)}")
    
    await state.finish()

async def parts_category_delete_list_callback(callback: types.CallbackQuery):
    """Список категорий для удаления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    categories = part_service.get_all_categories()
    
    if not categories:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="parts_categories_menu"))
        
        await callback.message.edit_text(
            "❌ Нет категорий для удаления",
            reply_markup=keyboard
        )
        return
    
    text = "🗑 <b>ВЫБЕРИТЕ КАТЕГОРИЮ ДЛЯ УДАЛЕНИЯ:</b>\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for cat in categories:
        if cat['count'] == 0:  # Только пустые категории можно удалить
            text += f"• {cat['name']} (пусто)\n"
            keyboard.add(InlineKeyboardButton(
                f"🗑 {cat['name']}",
                callback_data=f"parts_category_delete_{cat['id']}"
            ))
        else:
            text += f"• {cat['name']} - {cat['count']} запчастей (нельзя удалить)\n"
    
    text += "\n⚠️ Можно удалить только пустые категории"
    
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="parts_categories_menu"))
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

async def parts_category_delete_callback(callback: types.CallbackQuery):
    """Удаление категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[3])
    
    try:
        success, message_text = part_service.delete_category(category_id)
        
        if success:
            await callback.answer("✅ Категория удалена", show_alert=False)
            await callback.message.edit_text(
                f"✅ Категория удалена успешно!"
            )
        else:
            await callback.answer("❌ Ошибка", show_alert=True)
            await callback.message.edit_text(
                f"❌ {message_text}"
            )
            
    except Exception as e:
        logger.error(f"Ошибка при удалении категории: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)
        await callback.message.edit_text(
            f"❌ Ошибка при удалении категории"
        )
    
    # Возвращаемся в меню категорий
    await asyncio.sleep(1)
    await parts_categories_menu_callback(
        types.CallbackQuery(
            id="0",
            from_user=callback.from_user,
            message=callback.message,
            data="parts_categories_menu",
            chat_instance="0"
        )
    )

# ============================================
# УПРАВЛЕНИЕ ПОСТАВЩИКАМИ (ЕДИНСТВЕННАЯ ВЕРСИЯ)
# ============================================

async def parts_suppliers_menu_callback(callback: types.CallbackQuery):
    """Меню управления поставщиками"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    suppliers = part_service.get_all_suppliers()
    
    text = "🚚 <b>УПРАВЛЕНИЕ ПОСТАВЩИКАМИ</b>\n\n"
    
    if suppliers:
        for sup in suppliers:
            text += f"• <b>{sup['name']}</b>\n"
            text += f"  📞 {sup['phone'] or 'Не указан'}\n"
            text += f"  📦 Запчастей: {sup['parts_count']}\n\n"
    else:
        text += "Нет созданных поставщиков\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("➕ Добавить поставщика", callback_data="parts_supplier_add"),
        InlineKeyboardButton("🗑 Удалить поставщика", callback_data="parts_supplier_delete_list")
    )
    keyboard.add(
        InlineKeyboardButton("◀️ Назад", callback_data="parts_menu"),
        InlineKeyboardButton("◀️ В АДМИНКУ", callback_data="admin_menu")
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

async def parts_supplier_add_callback(callback: types.CallbackQuery, state: FSMContext):
    """Добавление нового поставщика"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    await state.finish()
    
    await callback.message.edit_text(
        "➕ <b>ДОБАВЛЕНИЕ НОВОГО ПОСТАВЩИКА</b>\n\n"
        "Шаг 1/5: Введите название компании/поставщика:\n"
        "Пример: <i>TechParts Ltd.</i>",
        parse_mode="HTML"
    )
    await PartStates.waiting_supplier_name.set()

async def process_supplier_name(message: types.Message, state: FSMContext):
    """Обработка названия поставщика"""
    if len(message.text.strip()) < 2:
        await message.answer("⚠️ Название слишком короткое. Введите минимум 2 символа:")
        return
    
    await state.update_data(supplier_name=message.text.strip())
    
    await message.answer(
        "Шаг 2/5: Введите контактное лицо (или отправьте '-' если не нужно):\n"
        "Пример: <i>Иван Петров</i>",
        parse_mode="HTML"
    )
    await PartStates.waiting_supplier_contact.set()

async def process_supplier_contact(message: types.Message, state: FSMContext):
    """Обработка контактного лица"""
    contact = message.text.strip()
    if contact == "-":
        contact = None
    
    await state.update_data(supplier_contact=contact)
    
    await message.answer(
        "Шаг 3/5: Введите телефон (или отправьте '-' если не нужно):\n"
        "Пример: <i>+992 900 123 456</i>",
        parse_mode="HTML"
    )
    await PartStates.waiting_supplier_phone.set()

async def process_supplier_phone(message: types.Message, state: FSMContext):
    """Обработка телефона"""
    phone = message.text.strip()
    if phone == "-":
        phone = None
    
    await state.update_data(supplier_phone=phone)
    
    await message.answer(
        "Шаг 4/5: Введите email (или отправьте '-' если не нужно):\n"
        "Пример: <i>info@techparts.tj</i>",
        parse_mode="HTML"
    )
    await PartStates.waiting_supplier_email.set()

async def process_supplier_email(message: types.Message, state: FSMContext):
    """Обработка email"""
    email = message.text.strip()
    if email == "-":
        email = None
    
    await state.update_data(supplier_email=email)
    
    await message.answer(
        "Шаг 5/5: Введите адрес (или отправьте '-' если не нужно):\n"
        "Пример: <i>г. Душанбе, ул. Айни 123</i>",
        parse_mode="HTML"
    )
    await PartStates.waiting_supplier_address.set()

async def process_supplier_address(message: types.Message, state: FSMContext):
    """Обработка адреса и создание поставщика"""
    data = await state.get_data()
    
    address = message.text.strip()
    if address == "-":
        address = None
    
    try:
        supplier_data = {
            "name": data["supplier_name"],
            "contact_person": data.get("supplier_contact"),
            "phone": data.get("supplier_phone"),
            "email": data.get("supplier_email"),
            "address": address,
            "notes": None
        }
        
        supplier = part_service.create_supplier(supplier_data)
        
        success_text = f"""✅ ПОСТАВЩИК УСПЕШНО ДОБАВЛЕН!

🏢 Название: {supplier.name}
👤 Контакт: {supplier.contact_person or 'Не указан'}
📞 Телефон: {supplier.phone or 'Не указан'}
📧 Email: {supplier.email or 'Не указан'}
📍 Адрес: {supplier.address or 'Не указан'}"""
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("➕ Еще поставщик", callback_data="parts_supplier_add")
        )
        keyboard.add(
            InlineKeyboardButton("◀️ В меню", callback_data="parts_suppliers_menu")
        )
        
        await message.answer(success_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при создании поставщика: {e}")
        
        if "already exists" in str(e).lower() or "уже существует" in str(e).lower():
            await message.answer(
                f"❌ Поставщик '{data['supplier_name']}' уже существует!"
            )
        else:
            await message.answer(
                f"❌ Ошибка при создании поставщика. Попробуйте позже."
            )
    
    await state.finish()

async def parts_supplier_delete_list_callback(callback: types.CallbackQuery):
    """Список поставщиков для удаления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    suppliers = part_service.get_all_suppliers()
    
    if not suppliers:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="parts_suppliers_menu"))
        
        await callback.message.edit_text(
            "❌ Нет поставщиков для удаления",
            reply_markup=keyboard
        )
        return
    
    text = "🗑 <b>ВЫБЕРИТЕ ПОСТАВЩИКА ДЛЯ УДАЛЕНИЯ:</b>\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    for sup in suppliers:
        if sup['parts_count'] == 0:  # Только поставщики без запчастей
            text += f"• {sup['name']} (нет запчастей)\n"
            keyboard.add(InlineKeyboardButton(
                f"🗑 {sup['name']}",
                callback_data=f"parts_supplier_delete_{sup['id']}"
            ))
        else:
            text += f"• {sup['name']} - {sup['parts_count']} запчастей (нельзя удалить)\n"
    
    text += "\n⚠️ Можно удалить только поставщиков без запчастей"
    
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="parts_suppliers_menu"))
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

async def parts_supplier_delete_callback(callback: types.CallbackQuery):
    """Удаление поставщика"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    supplier_id = int(callback.data.split("_")[3])
    
    try:
        success, message_text = part_service.delete_supplier(supplier_id)
        
        if success:
            await callback.answer("✅ Поставщик удален", show_alert=False)
            await callback.message.edit_text(
                f"✅ Поставщик удален успешно!"
            )
        else:
            await callback.answer("❌ Ошибка", show_alert=True)
            await callback.message.edit_text(
                f"❌ {message_text}"
            )
            
    except Exception as e:
        logger.error(f"Ошибка при удалении поставщика: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)
        await callback.message.edit_text(
            f"❌ Ошибка при удалении поставщика"
        )
    
    # Возвращаемся в меню поставщиков
    await asyncio.sleep(1)
    await parts_suppliers_menu_callback(
        types.CallbackQuery(
            id="0",
            from_user=callback.from_user,
            message=callback.message,
            data="parts_suppliers_menu",
            chat_instance="0"
        )
    )

# ============================================
# ПОИСК ЗАПЧАСТЕЙ
# ============================================

async def parts_search_callback(callback: types.CallbackQuery, state: FSMContext):
    """Поиск запчастей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    await callback.message.edit_text(
        "🔍 <b>ПОИСК ЗАПЧАСТЕЙ</b>\n\n"
        "Введите артикул или название запчасти:",
        parse_mode="HTML"
    )
    
    # Сохраняем сообщение для поиска
    await state.set_state("parts_search")

async def process_parts_search(message: types.Message, state: FSMContext):
    """Обработка поискового запроса"""
    query = message.text.strip().lower()
    
    if len(query) < 2:
        await message.answer("⚠️ Слишком короткий запрос. Введите минимум 2 символа:")
        return
    
    parts = part_service.get_all_parts()
    
    # Фильтруем запчасти
    found = []
    for part in parts:
        if (query in part['name'].lower() or 
            query in part['sku'].lower() or 
            (part['brand'] and query in part['brand'].lower())):
            found.append(part)
    
    if not found:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="parts_menu"))
        
        await message.answer(
            f"❌ По запросу <b>{message.text}</b> ничего не найдено",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await state.finish()
        return
    
    text = f"🔍 <b>РЕЗУЛЬТАТЫ ПОИСКА:</b> {len(found)}\n\n"
    
    for part in found[:5]:
        status_emoji = {
            "high": "✅",
            "medium": "⚡",
            "low": "⚠️",
            "out": "❌"
        }.get(part["status"], "📦")
        
        text += f"{status_emoji} <b>{part['name']}</b>\n"
        text += f"   📋 <code>{part['sku']}</code> - {part['stock']} шт.\n"
    
    if len(found) > 5:
        text += f"\n... и еще {len(found) - 5} запчастей\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔄 Новый поиск", callback_data="parts_search"))
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="parts_menu"))
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.finish()

# ============================================
# ПОПОЛНЕНИЕ ЗАПАСА
# ============================================

async def parts_restock_menu_callback(callback: types.CallbackQuery):
    """Меню пополнения запаса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    low_stock = part_service.get_low_stock_parts()
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    if low_stock:
        for part in low_stock[:5]:
            keyboard.add(InlineKeyboardButton(
                f"⚠️ {part['name']} (в наличии: {part['stock']})",
                callback_data=f"parts_restock_{part['id']}"
            ))
    
    keyboard.add(InlineKeyboardButton("🔍 Выбрать другую", callback_data="parts_search_for_restock"))
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="parts_menu"))
    
    await callback.message.edit_text(
        "📦 <b>ПОПОЛНЕНИЕ ЗАПАСА</b>\n\n"
        "Выберите запчасть для пополнения:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ============================================
# РЕГИСТРАЦИЯ ХЕНДЛЕРОВ
# ============================================

def register_parts_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков для запчастей"""
    
    # Команды
    dp.register_message_handler(cmd_parts, Command("parts"))
    dp.register_message_handler(cmd_parts, Text(equals="🔧 Запчасти"))
    
    # Callback-и для главного меню
    dp.register_callback_query_handler(parts_list_callback, text="parts_list")
    dp.register_callback_query_handler(parts_low_stock_callback, text="parts_low_stock")
    dp.register_callback_query_handler(parts_stats_callback, text="parts_stats")
    dp.register_callback_query_handler(parts_search_callback, text="parts_search")
    dp.register_callback_query_handler(parts_restock_menu_callback, text="parts_restock_menu")
    dp.register_callback_query_handler(cmd_parts, text="parts_menu")  # Возврат в меню
    
    # ===== КАТЕГОРИИ =====
    dp.register_callback_query_handler(parts_categories_menu_callback, text="parts_categories_menu")
    dp.register_callback_query_handler(parts_category_add_callback, text="parts_category_add", state="*")
    dp.register_callback_query_handler(parts_category_delete_list_callback, text="parts_category_delete_list")
    dp.register_callback_query_handler(
        parts_category_delete_callback, 
        lambda c: c.data and c.data.startswith("parts_category_delete_")
    )
    
    # States для категорий
    dp.register_message_handler(process_category_name, state=PartStates.waiting_category_name)
    dp.register_message_handler(process_category_description, state=PartStates.waiting_category_description)
    
    # ===== ПОСТАВЩИКИ =====
    dp.register_callback_query_handler(parts_suppliers_menu_callback, text="parts_suppliers_menu")
    dp.register_callback_query_handler(parts_supplier_add_callback, text="parts_supplier_add", state="*")
    dp.register_callback_query_handler(parts_supplier_delete_list_callback, text="parts_supplier_delete_list")
    dp.register_callback_query_handler(
        parts_supplier_delete_callback, 
        lambda c: c.data and c.data.startswith("parts_supplier_delete_")
    )
    
    # States для поставщиков
    dp.register_message_handler(process_supplier_name, state=PartStates.waiting_supplier_name)
    dp.register_message_handler(process_supplier_contact, state=PartStates.waiting_supplier_contact)
    dp.register_message_handler(process_supplier_phone, state=PartStates.waiting_supplier_phone)
    dp.register_message_handler(process_supplier_email, state=PartStates.waiting_supplier_email)
    dp.register_message_handler(process_supplier_address, state=PartStates.waiting_supplier_address)
    
    # ===== ЗАПЧАСТИ =====
    dp.register_callback_query_handler(parts_add_start, text="parts_add", state="*")
    dp.register_message_handler(process_part_name, state=PartStates.waiting_part_name)
    dp.register_message_handler(process_part_sku, state=PartStates.waiting_part_sku)
    dp.register_callback_query_handler(
        part_category_callback, 
        lambda c: c.data and c.data.startswith("part_cat_"), 
        state=PartStates.waiting_part_category
    )
    dp.register_message_handler(process_part_brand, state=PartStates.waiting_part_brand)
    dp.register_message_handler(process_part_purchase_price, state=PartStates.waiting_part_purchase_price)
    dp.register_message_handler(process_part_sale_price, state=PartStates.waiting_part_sale_price)
    dp.register_message_handler(process_part_stock, state=PartStates.waiting_part_stock)
    dp.register_message_handler(process_part_min_stock, state=PartStates.waiting_part_min_stock)
    
    # ===== ПОИСК =====
    dp.register_message_handler(process_parts_search, state="parts_search")
    
    logger.info("✅ Обработчики запчастей зарегистрированы")
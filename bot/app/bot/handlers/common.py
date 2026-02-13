# app/bot/handlers/common.py
from aiogram import types  # Добавьте этот импорт
from aiogram.dispatcher import Dispatcher  # Добавьте этот импорт
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext  # Добавьте этот импорт
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove  # Добавьте этот импорт
)
from app.bot.data.masters import MASTERS
from app.bot.data.categories import CATEGORIES
from app.bot.data.brands import BRANDS
from app.models.master import Master
from app.database import SessionLocal
from app.bot.data.masters import MASTERS

STATUS_FLOW = [
    "🧪 Диагностика",
    "🔧 В ремонте",
    "✅ Готово"
]

# ---------- keyboard builders ----------

def build_keyboard(items):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(i)] for i in items],
        resize_keyboard=True
    )

def build_master_keyboard(ticket_id, current_status=None):
    def btn(text, code):
        if text == current_status:
            return [InlineKeyboardButton(f"✔️ {text}", callback_data="disabled")]
        return [InlineKeyboardButton(text, callback_data=f"status_{code}_{ticket_id}")]
    
    return InlineKeyboardMarkup(inline_keyboard=[
        btn("🧪 Диагностика", "diag"),
        btn("🔧 В ремонте", "repair"),
        btn("✅ Готово", "done")
    ])

def build_master_select_keyboard(ticket_id):
    ticket_id = int(ticket_id)  # 🔒 защита
    rows = []
    
    for m in MASTERS:
        rows.append([
            InlineKeyboardButton(
                text=f"{m['name']} - {m['profession']}",
                callback_data=f"take:{ticket_id}:{m['telegram_id']}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_main_keyboard():
    """Клавиатура для администратора"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📥 Создать заявку")],
            [KeyboardButton("📊 Рейтинги мастеров")],
            [KeyboardButton("📋 Все заявки")],
            [KeyboardButton("👥 Мастера")]
        ],
        resize_keyboard=True
    )

def client_main_keyboard():
    """Клавиатура для клиента"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📥 Создать заявку")],
            [KeyboardButton("⏳ Статус ремонта")],
            [KeyboardButton("📋 Мои заявки")],
            [KeyboardButton("🔧 Запчасти")],
            [KeyboardButton("📅 Календарь"),  ]
            [KeyboardButton("ℹ️ О нас")],
            [KeyboardButton("💬 Поддержка")]
        ],
        resize_keyboard=True
    )

# Глобальные клавиатуры
branch_kb = build_keyboard(["🏢 Душанбе", "🏢 Худжанд"])
urgency_kb = build_keyboard(["⏳ Обычная", "🔥 Срочно"])

# Вспомогательные функции
def get_or_create_master(master_info):
    """Найти или создать мастера в базе"""
    db = SessionLocal()
    
    try:
        # Ищем мастера по telegram_id (теперь он есть в таблице)
        telegram_id_str = str(master_info.get('telegram_id', ''))
        
        if telegram_id_str:
            master = db.query(Master).filter(
                Master.telegram_id == telegram_id_str
            ).first()
            
            if master:
                print(f"Найден мастер по telegram_id: id={master.id}, name={master.name}")
                db.close()
                return master
        
        # Если не нашли по telegram_id, ищем по имени
        master = db.query(Master).filter(
            Master.name == master_info['name']
        ).first()
        
        if master:
            # Обновляем telegram_id если его нет
            if not master.telegram_id and telegram_id_str:
                master.telegram_id = telegram_id_str
                db.commit()
                print(f"Обновлен telegram_id для мастера {master.id}")
            
            print(f"Найден мастер по имени: id={master.id}, name={master.name}")
            db.close()
            return master
        
        # Создаем нового мастера
        print(f"Создаем нового мастера с данными: {master_info}")
        
        master = Master(
            name=master_info['name'],
            surname=master_info.get('surname', ''),
            phone=str(master_info.get('phone', '')),  # Если есть phone в данных
            telegram_id=telegram_id_str,  # Используем поле telegram_id
            specialization=master_info.get('profession', ''),  # profession -> specialization
            experience=master_info.get('experience', 0),
            status='active',
            rating=0.0,
            skills=master_info.get('skills', ''),
            active_orders=0,
            completed_orders=0,
            rating_count=0
        )
        
        db.add(master)
        db.commit()
        db.refresh(master)
        print(f"Создан новый мастер: id={master.id}, name={master.name}, telegram_id={master.telegram_id}")
        
        return master
        
    except Exception as e:
        print(f"Ошибка при поиске/создании мастера: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()

def register_common_handlers(dp: Dispatcher):  # Добавьте аннотацию типа
    @dp.message_handler(commands=['start', 'help'])
    async def send_welcome(message: types.Message):
        # Убираем импорты внутри функции, они уже в начале файла
        from app.bot.config import ADMIN_IDS
        
        welcome_text = """
🤖 Добро пожаловать в сервисный центр!

С помощью этого бота вы можете:
• 📥 Создать заявку на ремонт
• 📋 Отслеживать статус заявок
• ⭐ Оценить работу мастеров
• ℹ️ Узнать информацию о сервисе
"""
        
        if message.from_user.id in ADMIN_IDS:
            await message.answer(welcome_text, reply_markup=admin_main_keyboard())
        else:
            await message.answer(welcome_text, reply_markup=client_main_keyboard())
    
    @dp.message_handler(commands=['cancel'], state='*')
    async def cancel_handler(message: types.Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state is None:
            return
        
        await state.finish()
        await message.answer('❌ Действие отменено', reply_markup=ReplyKeyboardRemove())

    # app/bot/handlers/common.py - обновим функцию

def client_main_keyboard():
    """Основная клавиатура для клиента"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📥 Создать заявку"), KeyboardButton("📋 Мои заявки")],
            [KeyboardButton("⏳ Статус ремонта"), KeyboardButton("ℹ️ О нас")],
            [KeyboardButton("📞 Контакты"), KeyboardButton("💬 Поддержка")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False  # Чтобы клавиатура оставалась
    )    
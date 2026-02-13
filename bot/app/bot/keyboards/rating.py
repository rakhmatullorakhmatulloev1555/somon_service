from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def rating_keyboard(master_id):

    kb = InlineKeyboardMarkup()

    for i in range(1,6):
        kb.add(
            InlineKeyboardButton(
                text=f"{i}⭐",
                callback_data=f"rate_{master_id}_{i}"
            )
        )

    return kb

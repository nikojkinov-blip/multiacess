from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from typing import List, Tuple

def create_inline_keyboard(
    buttons: List[Tuple[str, str]],
    row_width: int = 2
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for text, callback_data in buttons:
        builder.button(text=text, callback_data=callback_data)
    builder.adjust(row_width)
    return builder.as_markup()
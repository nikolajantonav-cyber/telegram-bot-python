
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔍 Поиск рецептов"), KeyboardButton("➕ Добавить рецепт"))
    kb.add(KeyboardButton("👣 Учение рецептов"), KeyboardButton("📖 Все рецепты"))
    kb.add(KeyboardButton("🗑️ Удалить рецепты"), KeyboardButton("📊 Статистика"))
    kb.add(KeyboardButton("🎲 Случайный рецепт"), KeyboardButton("🧠 Совет от шефа"))
    kb.add(KeyboardButton("🥗 Из ингредиентов?"), KeyboardButton("⏱️ Быстрое блюдо"))
    kb.add(KeyboardButton("📅 Рацион на 3 дня"))

    kb.add(KeyboardButton("⭐ Избранное"), KeyboardButton("🧾 Список покупок"))
    return kb

def cook_button(recipe_id: int):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🍳 Хочу готовить", callback_data=f"cook:{recipe_id}:0"))
    return kb

def next_step_btn(recipe_id: int, step_idx: int):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➡️ Далее", callback_data=f"cook:{recipe_id}:{step_idx}"))
    return kb
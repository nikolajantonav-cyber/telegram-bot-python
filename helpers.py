import json, logging, os
from typing import List, Dict, Any
from aiogram import types
from config import CUT_CAL_TARGET, BULK_CAL_TARGET, RECIPES_JSON_PATH
import db


"""  Форматирование ингредиентов и карточек  """

def fmt_ingredients(ings: List[Dict[str, Any]]) -> str:
    lines = ["<u>Ингредиенты (с граммовками и ккал):</u>"]
    for i in ings:
        name = i.get("name", "?")
        grams = int(float(i.get("grams", 0)))
        kcal = int(float(i.get("kcal", 0)))
        lines.append(f"• {name} — {grams} г ({kcal} ккал)")
    return "\n".join(lines)

def fmt_card_short(row) -> str:
    ings = json.loads(row["ingredients_json"])
    return (f"<b>{row['title']}</b>\n"
            f"{row['description']}\n\n"
            f"⏱️ Время: <b>{row['cook_time_min']} мин</b>\n"
            f"⚖️ Выход: <b>{row['total_grams']} г</b>\n"
            f"🔥 Калории: <b>{row['total_kcal']} ккал</b>\n\n"
            f"{fmt_ingredients(ings)}\n\n"
            f"Нажми кнопку снизу, если хочешь готовить пошагово ⤵️")





'''🧠 Советы шефа'''

def chef_tip() -> str:
    import random
    tips = [
        "Пробуйте на кислотность: капля лимона часто «собирает» вкус блюда.",
        "Пасту варите на минуту меньше — доготовится в соусе (аль денте).",
        "Даёте мясу «отдохнуть» 5–10 минут — соки распределятся равномерно.",
        "Соль добавляйте постепенно — легче довести вкус, чем исправлять пересол.",
        "Овощи обжаривайте партиями — так они не тушатся в собственном соку."
    ]
    return "🧠 Совет от шефа:\n" + random.choice(tips)


''' План питания'''


def plan_3_days(goal: str) -> str:
    if goal == "Похудение":
        target = CUT_CAL_TARGET
        days = [
            ["Овсяная каша с бананом 🍌", "Огуречный салат с йогуртом 🥒", "Курица с рисом 🍗🍚"],
            ["Сырники классические 🧀", "Салат «Цезарь» 🥗", "Тушёная рыба с рисом 🐟🍚"],
            ["Омлет с томатами 🍳", "Паста с томатами 🍝", "Греческий салат 🧀🥗"],
        ]
    else:
        target = BULK_CAL_TARGET
        days = [
            ["Панкейки 🥞 + мёд", "Плов узбекский 🍚🥩", "Карбонара 🍝"],
            ["Борщ украинский 🍲 + хлеб", "Котлеты с пюре 🥔", "Пицца «Маргарита» 🍕"],
            ["Сырники 🧀 + сметана", "Паста болоньезе 🍝", "Курица с гречкой 🍗+🍚"],
        ]
    out = [f"📅 <b>Рацион на 3 дня — {goal}</b>\nЦель по калорийности: {target}\n"]
    for d, m in enumerate(days, 1):
        out.append(f"<u>День {d}</u>:\n• Завтрак: {m[0]}\n• Обед: {m[1]}\n• Ужин: {m[2]}")
    return "\n".join(out)


'''📦 Импорт рецептов из JSON'''


def load_recipes_from_json(path: str = RECIPES_JSON_PATH) -> int:
    """Импорт из JSON в базу (user_id = NULL). Возвращает число добавленных."""
    if not os.path.exists(path):
        logging.info(f"JSON не найден: {path}")
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items: List[Dict[str, Any]] = []
        for r in data:
            if not all(k in r for k in ("title", "description", "ingredients", "steps", "cook_time_min")):
                continue
            items.append({
                "title": r["title"],
                "description": r["description"],
                "ingredients": r["ingredients"],
                "steps": r["steps"],
                "cook_time_min": int(r["cook_time_min"])
            })
        if items:
            db.insert_many(items)
        logging.info(f"Импортировано рецептов из JSON: {len(items)}")
        return len(items)
    except Exception as e:
        logging.exception(f"Ошибка импорта JSON: {e}")
        return 0